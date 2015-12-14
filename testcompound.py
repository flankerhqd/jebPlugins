#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'qidan.hqd@alibaba-inc.com'

from jeb.api import IScript
from jeb.api.ui import View
from collections import defaultdict
class testcompound(IScript):
    def run(self, j):
            self.instance = j
            self.dex = j.getDex()
            self.renameCnt = 0
            sig = self.instance.getUI().getView(View.Type.JAVA).getCodePosition().getSignature()
            self.alteredClz = set()

            for i in self.dex.getClassSignatures(True):
                self.instance.print("processing "+i)
                cls = self.dex.getClass(i)
                if cls.getData():
                    dexMethodDatas = cls.getData().getVirtualMethods()
                    for dexMethodData in dexMethodDatas:
                        methodName = self.dex.getMethod(dexMethodData.getMethodIndex()).getName()
                        self.instance.print(str(methodName))
                        currentMethod = self.instance.getDecompiledMethodTree(sig)

                        body = currentMethod.getBody()
                        for i in range(body.size()):
                            self.scanStatement(body.get(i))

    def scanStatement(self,stmt):
        self.viewElement(stmt,1)

    def viewElement(self, element, depth):
        self.instance.print("    "*depth+repr(element))
        for sub in element.getSubElements():
            self.viewElement(sub, depth+1)
