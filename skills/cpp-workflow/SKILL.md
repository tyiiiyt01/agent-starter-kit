---
name: cpp-workflow
description: 帮用户完成 C/C++ 的编译运行闭环（选编译器、编译、读编译与链接错误、修、重编），按平台给出 clang++/g++/cl 的正确命令；并处理 MATLAB 无授权时用 Octave 运行 .m 文件。当用户要编译运行 C/C++、遇到编译或链接报错，或要跑 MATLAB 脚本却没有 MATLAB 时使用。
---

# C++ / MATLAB 编译运行工作流

## 1. 先确定编译器（按平台）

不同平台编译器不同，不要照搬命令：

| 平台 | 首选命令 | 获取方式 |
|---|---|---|
| macOS | `clang++` | `xcode-select --install`（会弹系统确认框，需用户点安装） |
| Windows | `g++`（MinGW-w64） | 装 MinGW-w64 |
| Windows | `cl`（MSVC） | 装 Visual Studio Build Tools |
| Linux | `g++` | 发行版包管理器 |

先探测：`clang++ --version` / `g++ --version` / `cl`。
（MSVC 的 `cl` 只在「开发者命令提示符」里可用，普通终端找不到属正常。）

编 C++ 源文件（`.cpp`）要用 C++ 编译器（`clang++` / `g++`），**不要**用 C 的 `gcc` 去编 `.cpp`，容易漏掉 C++ 运行时库，引出一堆链接错误。

## 2. 标准编译运行命令

macOS / Linux：

```bash
clang++ -std=c++17 -Wall -Wextra -O2 -o prog main.cpp && ./prog
# 或
g++ -std=c++17 -Wall -Wextra -O2 -o prog main.cpp && ./prog
```

Windows（MinGW g++）：

```bat
g++ -std=c++17 -Wall -Wextra -O2 -o prog.exe main.cpp && prog.exe
```

Windows（MSVC cl，在开发者命令提示符内）：

```bat
cl /std:c++17 /EHsc /W4 /Fe:prog.exe main.cpp && prog.exe
```

说明：

- `-Wall -Wextra` 打开常用警告，很多「能编过但结果不对」的问题就藏在这里
- 多文件：`clang++ -std=c++17 -o prog a.cpp b.cpp main.cpp`
- 需要数学库时 Linux 加 `-lm`；用线程加 `-pthread`

## 3. 读编译错误的顺序

编译器报错**从第一条开始看**（后面的错误常常是第一条的连锁反应）。

- 看 `file:line:column`，直接定位到行列
- 若报错文件是系统头文件，往上找**第一条出现在用户源码里的**错误
- 模板报错超长时，只看最前面一两行和最后的 `note:`，抓关键字

常见错误对照：

| 报错 | 原因 | 修法 |
|---|---|---|
| `'xxx' was not declared in this scope` | 变量/函数未定义、拼错或作用域不对 | 补 `#include`，检查拼写与作用域 |
| `expected ';' before ...` | 上一行漏分号 | 看报错行的**上一行** |
| `no matching function for call` | 参数类型或数量不匹配 | 看候选签名，核对实参类型 |
| `undefined reference to 'xxx'` | **链接**错误：声明了但没实现或没链接库 | 补实现文件，或加 `-l<库>` |
| `fatal error: 'xx.h' file not found` | 头文件路径不对 | 用 `-I<目录>` 指定，或装对应开发库 |
| `use of undeclared identifier 'cout'` | 缺 `#include <iostream>` 或少 `std::` | 补头文件，或加 `using namespace std;` |

运行期崩溃时：

- 段错误（Segmentation fault）多为数组越界、空指针、悬垂指针
- 用 `clang++ -g -fsanitize=address`（或 `g++ -g -fsanitize=address`）重编，能直接指出越界位置
- 死循环或卡住用调试器：`lldb ./prog` 或 `gdb ./prog`

## 4. 修完重编，贴真实输出

改完必须重新编译并运行，把编译结果和程序输出给用户看。要区分「编译通过」和「结果正确」，这是两回事。

## 5. MATLAB 无授权时的降级：Octave

MATLAB 需要商业授权、体积巨大，不引导用户安装。先探测：

- `matlab -h` 能跑 → 有 MATLAB，直接用
- `octave --version` 能跑 → 用 Octave 跑 `.m` 兼容语法
- 都没有 → 告诉用户「有学校授权就装 MATLAB；不想装可以用 Octave 跑大部分语法」

Octave 运行 `.m`：

```bash
octave --no-gui script.m          # 直接跑脚本
octave --eval "x=1:5; disp(x)"    # 跑一行
```

兼容性注意（Octave 不是 MATLAB 的完全替身）：

- 多数基础语法、矩阵运算、`plot`、`disp`、`for/while/if` 通用
- 工具箱函数（部分 `signal` / `stats` 函数）、App Designer、Simulink **没有**
- `end` 索引、`%` 注释通用；函数文件命名规则一致（文件名 = 函数名）
- 遇到「不认识某函数」，先确认它属于哪个 toolbox；多数工具箱函数 Octave 不可用，需改用基础写法实现，不要硬编一个不存在的替代命令