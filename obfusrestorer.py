#? name=De-obfuscator, shortcut=Ctrl+Shift+O, help=fire the plugin to try to automatically restore proguarded fields from IDE-generated toString methods

__author__ = 'hqd'
from jeb.api import IScript
from jeb.api.ast import Assignment, Block, Call, Class, Compound, ConditionalExpression
from jeb.api.ast import Constant, Expression, IElement, IExpression, InstanceField, Predicate, StaticField
from jeb.api.ast import Method, Return, Statement
from jeb.api.ui import View
import re

def replaceNonApplicableChars(s):
    return re.sub('[^0-9a-zA-Z]+', ' ', s)

class obfusrestorer(IScript):

    def run(self, j):
        self.instance = j
        self.dex = j.getDex()
        self.renameCnt = 0
        self.alteredClz = set()

        for i in self.dex.getClassSignatures(True):
            self.instance.print("processing "+i)
            cls = self.dex.getClass(i)
            if cls.getData():
                dexMethodDatas = cls.getData().getVirtualMethods()
                for dexMethodData in dexMethodDatas:
                    currentMethod = self.dex.getMethod(dexMethodData.getMethodIndex())
                    methodName = currentMethod.getName()
                    if methodName == "toString":
                        self.instance.print("scanning method: " + currentMethod.getSignature(True))#effective name
                        self.refactorUseToString(currentMethod.getBody())

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
                self.instance.print(rightexp.getField().getSignature())
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
                            self.instance.renameField(statement.getLeft().getField().getSignature(), name)
                            self.instance.print("rename from " + statement.getLeft().getField().getSignature() + " to "
                                                + name)
                            #use first found string, so break here
                            break
        if isinstance(statement, Compound):
            map(self.refactorUseCallArg, statement.getBlocks())

    def refactorUseToString(self, block):
        '''
        e.g. "##### VoDownloadEx2 ##### \nmDownLoadURI          : " + this.b + "\n" + "mContentsSize         : "
                 + this.c + "\n" + "mInstallSize          : "
        e.g. return "UpdateEntity [info=" + this.a + ", name=" + this.name + ", size=" + this.size + ", type="
                 + this.type + ", url=" + this.url + ", version=" + this.version + ", pri=" + this.pri
                 + ", md5=" + this.md5 + "]";
        :param block:
        :return:
        '''
        if block.size() >= 0 and isinstance(block.get(0), Return):
            #exp is the return expression
            exp = block.get(0).getExpression()

            while True:
                right = exp.getRight()

                #filter out cases like "test: " + this.d + " ]", remove trailing strings
                #e.g. return "Entity [info="+this.a+"aaa"+"bbb"
                #notice exp.getRight() here returns "bbb", exp.getLeft() returns "Entity [info="+this.a+"aaa"
                while isinstance(right, Constant):
                    exp = exp.getLeft()
                    #todo check if right is empty str
                    right = exp.getRight()

                right = exp.getRight()
                left = exp.getLeft()

                if isinstance(left, Constant):
                    #we have reached the left end of whole return expression
                    left = left.getString()
                    left = replaceNonApplicableChars(left)
                    lefts = left.split()

                    #nasty processing based on Eclipse-generated-toString style
                    firstFieldName = lefts[-1].strip()
                    firstField = right
                    possibleClzName = None if len(lefts) < 2 else lefts[0]
                    if isinstance(firstField, InstanceField):
                        self.instance.renameField(firstField.getField().getSignature(), firstFieldName)
                        #attach tag for getter/setter rename use
                        firstField.getField().attachTag("name", firstFieldName)
                        self.instance.print("rename from " + firstField.getField().getSignature() + " to " + firstFieldName)
                        self.alteredClz.add(self.getClzFromField(firstField))

                        if possibleClzName:
                            self.instance.renameClass(self.getClzFromField(firstField).getType(), possibleClzName)
                    break
                else:
                    #doing left traversal
                    #e.g. return {"Entity [info="+this.a+}(left.left)"value="(left.right)+this.b(right)
                    leftStr = filter(lambda c: c.isalpha() or c.isdigit() or c.isspace(), left.getRight().getString()).strip()
                    self.renamePossibleExpressionWithStr(right, leftStr)
                    exp = left.getLeft()


    def renamePossibleExpressionWithStr(self, exp, name):
        if isinstance(exp, InstanceField) or isinstance(exp, StaticField):
            self.instance.renameField(exp.getField().getSignature(), name)
            self.instance.print("rename from " + exp.getField().getSignature() + " to " + name)
            exp.getField().attachTag("name", name)
            self.alteredClz.add(self.getClzFromField(exp))
        elif isinstance(exp, Call) or isinstance(exp, ConditionalExpression) or isinstance(exp, Predicate): #consider this.a.toString(), need extract this.a
            targetFields = filter(lambda s: isinstance(s, InstanceField), exp.getSubElements())
            if len(targetFields) >= 1:
                self.renamePossibleExpressionWithStr(targetFields[0], name)
        else:
            #whoops, what's that
            pass


    def getClzFromField(self, iField):
        fieldSig = iField.getField().getSignature()
        return self.instance.getDecompiledClassTree(fieldSig.split(';')[0])






