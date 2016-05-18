# jebPlugins
Various Jeb plugins, including obfuscation restore 
Tested on newest JEB1 20150810
##Note: JEB2 has changed a lot in the API, not applicable to JEB2.
Current included: 

Source Info Restorer. Restore class name from proguarded output.

Deobfuscator. Restore field names from toString method and call statement with string arguments

Example:

```
.class public a
.super VolleyError
.source "TimeoutError.java"
```
can be used to restore *a* to its origin name *TimeoutError*

Example:
```
        e.g. "##### VoDownloadEx2 ##### \nmDownLoadURI          : " + this.b + "\n" + "mContentsSize         : "
                 + this.c + "\n" + "mInstallSize          : "
        e.g. return "UpdateEntity [info=" + this.a + ", name=" + this.name + ", size=" + this.size + ", type="
                 + this.type + ", url=" + this.url + ", version=" + this.version + ", pri=" + this.pri
                 + ", md5=" + this.md5 + "]";
```
Can be used to restore `this.b` `this.c` to `this.DownLoadURI` `this.mContentsSize`
## License

[jebPlugins] use [SATA License](LICENSE.txt) (Star And Thank Author License), so you have to star this project before using. Read the [license](LICENSE.txt) carefully.
