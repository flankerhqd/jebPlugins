__author__ = 'hqd'
#com.samsung.android.themestore.openapi.response.vo
from jeb.api import IScript
from jeb.api.ast import Assignment, Block, Call, Class, Compound
from jeb.api.ast import Constant, Expression, IElement, IExpression, InstanceField
from jeb.api.ast import Method, Return, Statement
from jeb.api.ui import View
import re

def replaceNonApplicableChars(s):
    return re.sub('[^0-9a-zA-Z]+', ' ', s)
class beanfucker(IScript):

    def run(self, j):
        self.instance = j
        self.renameCnt = 0
        sig = self.instance.getUI().getView(View.Type.JAVA).getCodePosition().getSignature()
        self.alteredClz = set()


        currentMethod = self.instance.getDecompiledMethodTree(sig)
        self.instance.print("scanning method: " + currentMethod.getSignature())

        if currentMethod.getName() == "toString":
            self.refactorUseToString(currentMethod.getBody())
        else:
            self.refactorUseCallArg(currentMethod.getBody())

        map(self.rebuildGetterAndSetters, [cm for clz in self.alteredClz for cm in clz.getMethods()])
        self.instance.getUI().getView(View.Type.JAVA).refresh()
        self.instance.getUI().getView(View.Type.ASSEMBLY).refresh()
        self.instance.getUI().getView(View.Type.CLASS_HIERARCHY).refresh()

    def rebuildGetterAndSetters(self, cm):
        '''
        rebuild getter and setters
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
        :return:
        '''
        for i in range(block.size()):
            self.scanStatement(block.get(i))

    def scanStatement(self, statement):
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
                            self.renameCnt += 1
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
            #first retrive left
            exp = block.get(0).getExpression()

            while True:
                right = exp.getRight()

                #filter out cases like "test: " + this.d + " ]"
                while isinstance(right, Constant):
                    exp = exp.getLeft()
                    #todo check if right is empty str
                    right = exp.getRight()

                right = exp.getRight()
                left = exp.getLeft()

                if isinstance(left, Constant):
                    #we have reached the left end of this expression
                    left = left.getString()
                    left = replaceNonApplicableChars(left)
                    lefts = left.split()

                    firstFieldName = lefts[-1].strip()
                    firstField = right
                    possibleClzName = None if len(lefts) < 2 else lefts[0]
                    if isinstance(firstField, InstanceField):
                        self.instance.renameField(firstField.getField().getSignature(), firstFieldName)
                        firstField.getField().attachTag("name", firstFieldName)
                        self.instance.print("rename from " + firstField.getField().getSignature() + " to " + firstFieldName)
                        self.alteredClz.add(self.getClzFromField(firstField))

                        if possibleClzName:
                            self.instance.renameClass(self.getClzFromField(firstField).getType(), possibleClzName)
                    break
                else:
                    #doing left traversal
                    leftStr = filter(lambda c: c.isalpha() or c.isdigit() or c.isspace(), left.getRight().getString()).strip()
                    self.instance.print(right.toString())
                    self.instance.print(str(right.getSubElements()))
                    if isinstance(right, InstanceField):
                        self.instance.renameField(right.getField().getSignature(), leftStr)
                        self.instance.print("rename from " + right.getField().getSignature() + " to " + leftStr)
                        right.getField().attachTag("name", leftStr)
                        self.alteredClz.add(self.getClzFromField(right))
                    elif isinstance(right, Call): #consider this.a.toString()
                        targetFields = filter(lambda s: isinstance(s, InstanceField), right.getSubElements())
                        if len(targetFields) >= 1:
                            self.instance.renameField(targetFields[0].getField().getSignature(), leftStr)
                            self.instance.print("rename from " + targetFields[0].getField().getSignature() + " to " + leftStr)
                            targetFields[0].getField().attachTag("name", leftStr)
                            self.alteredClz.add(self.getClzFromField(targetFields[0]))
                    elif isinstance(right, Compound):
                        #TODO this.a?test:test
                        pass
                    exp = left.getLeft()


    def getClzFromField(self, iField):
        fieldSig = iField.getField().getSignature()
        return self.instance.getDecompiledClassTree(fieldSig.split(';')[0])






