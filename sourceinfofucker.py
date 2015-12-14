__author__ = 'flanker'
'''
Util to extract Source info from dex and restore class name from proguard
'''
from jeb.api import IScript
from jeb.api.ui import View
from collections import defaultdict

class sourceinfofucker(IScript):

    def run(self, j):
        self.instance = j
        self.dex = j.getDex()

        pool = defaultdict(list)

        #ignore invalid source, i.e. "proguard" and other self-defined string
        for i in self.dex.getClassSignatures(True):
            cls = self.dex.getClass(i)
            if i.startswith(u"com/a/a/a/a"):
            	print origin
            if cls == None:
            	self.instance.print("error in resolving " + i + " skipping")
            	#oops, wtf
            	continue
            sourceIdx = cls.getSourceIndex()
            if sourceIdx != -1:
                source = self.dex.getString(sourceIdx)
                if source == "" or source.lower() == "proguard":
                    continue
                if source.endswith(".java"):
                    source = source[:-5]
                pool[source].append(i)

        if len(pool.keys()) == 0:
            self.instance.print("fuck! no class source info found.")
        elif len(pool.keys()) <= 2:
            #less than two distinct keys, we're fooled
            self.instance.print("fuck! we're fooled by %s. Stopping now" % pool.keys()[0])
        else:
            self.instance.print("renaming %d classes"%(len(pool.keys())))
            for k, v in pool.iteritems():
                for origin in v:
                    #notice some inner class may share same Source Info
                    if origin.find(u"$") != -1:
                    	#this is a inner class, proceed with caution
                    	k = k + "$" + origin.split('$')[1]
                    if origin.startswith(u"Lcom/a/a/a/a"):
                    	self.instance.print("renaming from %s to %s" % (origin,k))
                    self.instance.renameClass(origin, k)
            self.instance.print("renaming done")

            self.instance.getUI().getView(View.Type.JAVA).refresh()
            self.instance.getUI().getView(View.Type.ASSEMBLY).refresh()
            self.instance.getUI().getView(View.Type.CLASS_HIERARCHY).refresh()