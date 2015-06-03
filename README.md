# jebPlugins
Various Jeb plugins, including obfuscation restore 

Current included: Source Info Restorer. Restore class name from proguarded output.
Example:

```
.class public a
.super VolleyError
.source "TimeoutError.java"
```
can be used to restore *a* to its origin name *TimeoutError*

To be added: De-obfuscator

## License

[jebPlugins] use [SATA License](LICENSE.txt) (Star And Thank Author License), so you have to star this project before using. Read the [license](LICENSE.txt) carefully.
