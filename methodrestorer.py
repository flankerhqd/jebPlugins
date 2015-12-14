#? name=Method-obfuscator, shortcut=Ctrl+Shift+M, help=try to recover field names and variable names from string arguments, place caret in method body to try to restore all stmts in method

__author__ = 'hqd'
from jeb.api import IScript
from jeb.api.ast import Assignment, Block, Call, Class, Compound, ConditionalExpression
from jeb.api.ast import Constant, Expression, IElement, IExpression, InstanceField, Predicate, StaticField
from jeb.api.ast import Method, Return, Statement
from jeb.api.ui import View
import re

def replaceNonApplicableChars(s):
    return re.sub('[^0-9a-zA-Z]+', '_', s)

class methodrestorer(IScript):

    def run(self, j):
        self.instance = j
        self.dex = j.getDex()
        self.renameCnt = 0
        sig = self.instance.getUI().getView(View.Type.JAVA).getCodePosition().getSignature()
        currentMethod = self.instance.getDecompiledMethodTree(sig)
        self.alteredClz = set()

        self.refactorUseCallArg(currentMethod.getBody())
        map(self.rebuildGetterAndSetters, [cm for clz in self.alteredClz for cm in clz.getMethods()])

        self.instance.getUI().getView(View.Type.JAVA).refresh()
        self.instance.getUI().getView(View.Type.ASSEMBLY).refresh()
        self.instance.getUI().getView(View.Type.CLASS_HIERARCHY).refresh()

    def rebuildGetterAndSetters(self, cm):
        '''
        rebuild getter and setters e.g void a(object o){this.a = o;} to void setA(object o);
        :type cm: Method
        :param cm: target method to rename
        :return: None
        '''
        if cm.getBody().size() != 1:
            return
        stmt = cm.getBody().get(0)
        if isinstance(stmt, Return):
            rightexp = stmt.getExpression()
            if isinstance(rightexp, InstanceField):
                #we find a "getter" method, rename the method name
                name = rightexp.getField().getName()
                tagName = rightexp.getField().retrieveTag("name")
                #use tagName generated from toString if applicable, or use original name instead
                targetName = tagName if tagName else name
                self.instance.renameMethod(cm.getSignature(), "get" + targetName.title())
        elif isinstance(stmt, Assignment):
            leftexp = stmt.getLeft()
            if isinstance(leftexp, InstanceField):
                #we find a "setter" method, rename the method name
                name = leftexp.getField().getName()
                tagName = leftexp.getField().retrieveTag("name")
                targetName = tagName if tagName else name
                self.instance.renameMethod(cm.getSignature(), "set" + targetName.title())


    def refactorUseCallArg(self, block):
        '''
        	/*
	 * The layout of JEB syntax tree is like:
	 *
	 * BLOCK => {
	 * 			STMT => (SubElements => left, right)
	 * 			STMT => (SubElements => left, right)
	 * 			COMPOUND_STMT(IF) => (subElements)
	 * 								BLOCK => {
	 * 										STMT
	 * 										STMT
	 * 								}
	 * 			STMT
	 * }
	 *
	 */
        :param block:
        :return: void
        '''
        for i in range(block.size()):
            self.scanStatement(block.get(i))

    def scanStatement(self, statement):
        '''
        refactor this.a = jsonobj.getJsonString("fancyName") to this.fancyName
        TODO add variable name rename support??
        :param statement: statement to scan
        :return: void
        '''
        if isinstance(statement, Assignment):
            if isinstance(statement.getLeft(), InstanceField):
                if isinstance(statement.getRight(), Call):
                    args = statement.getRight().getArguments()
                    for arg in args:
                        if isinstance(arg, Constant) and arg.isString():
                            name = arg.getString()
                            name = replaceNonApplicableChars(name)
                            self.instance.renameField(statement.getLeft().getField().getSignature(), name)
                            self.instance.print("rename from " + statement.getLeft().getField().getSignature() + " to "
                                                + name)
                            statement.getLeft().getField().attachTag("name", name)
                            self.alteredClz.add(self.getClzFromField(statement.getLeft().getField()))
                            #use first found string, so break here
                            break
        if isinstance(statement, Compound):
            map(self.refactorUseCallArg, statement.getBlocks())

    def getClzFromField(self, iField):
        fieldSig = iField.getSignature()
        return self.instance.getDecompiledClassTree(fieldSig.split(';')[0])






