https://stackoverflow.com/a/10199440/2999096

```
#pragma init_seg
```
是VC++特有的

g++不能用，但有个类似的：
```
Some_Class  A  __attribute__ ((init_priority (2000)));
Some_Class  B  __attribute__ ((init_priority (543)));
```
