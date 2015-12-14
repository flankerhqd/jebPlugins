# jebPlugins
Various Jeb plugins, including obfuscation restore 
##Note: JEB1 has changed a lot since writing, not applicable to new versions of JEB.
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


## License

[jebPlugins] use [SATA License](LICENSE.txt) (Star And Thank Author License), so you have to star this project before using. Read the [license](LICENSE.txt) carefully.
