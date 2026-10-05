# 选择题 + 简答题

> 本文件包含所有选择题与简答题，请在你的仓库中于本文件作答。
> **硬性要求：本文件所有题目均必须完成，未完成的题目不进入部门筛选流程。**

## 一、选择题（每题 2 分，共 10 题，满分 20 分）

> 说明：单选，将答案写在本节末尾的「答案」行中，格式如 `1. A  2. B  3. C ...`。

1. 依次执行以下代码，输出是什么？

   ```python
   def f(x, lst=[]):
       lst.append(x)
       return lst

   a = f(1)
   b = f(2)
   print(b)
   ```

   - A. `[2]`
   - B. `[1, 2]`
   - C. `[1]`
   - D. `TypeError: 'list' object is not callable`

   > **B**。默认参数 `lst=[]` 只在函数**定义时**求值一次，`a` 和 `b` 共享同一个列表对象，所以第二次调用得到 `[1, 2]`。

2. 依次执行以下代码，输出是什么？

   ```python
   a = [1, 2, 3]
   b = a
   c = a.copy()
   a.append(4)
   print(b, c)
   ```

   - A. `[1, 2, 3, 4]  [1, 2, 3, 4]`
   - B. `[1, 2, 3, 4]  [1, 2, 3]`
   - C. `[1, 2, 3]  [1, 2, 3, 4]`
   - D. `[1, 2, 3]  [1, 2, 3]`

   > **B**。`b = a` 只是新增一个名字指向同一对象（引用绑定），`c = a.copy()` 才是新列表。

3. 依次执行以下代码，输出是什么？

   ```python
   try:
       x = 1 / 0
   except ZeroDivisionError:
       print("A")
   else:
       print("B")
   finally:
       print("C")
   ```

   - A. 只输出 `C`
   - B. 输出 `A` 和 `C`
   - C. 输出 `B` 和 `C`
   - D. 输出 `A`、`B` 和 `C`

   > **B**。`else` 子句只在 try 块**没有**抛异常时执行；`finally` 无论如何都执行。

4. 依次执行以下代码，输出是什么？

   ```python
   s = " hello "
   print(len(s))
   print(len(s.strip()))
   ```

   - A. `7  7`
   - B. `7  5`
   - C. `5  5`
   - D. `5  7`

   > **B**。`" hello "` 长度为 7（首尾各一个空格）；`strip()` 去掉首尾空白后为 `"hello"`，长度 5。

5. 以下代码的执行结果是？

   ```python
   for i in range(5):
       if i == 3:
           break
   else:
       print("done")
   print("end")
   ```

   - A. 输出 `done` 和 `end`
   - B. 只输出 `end`
   - C. 只输出 `done`
   - D. 什么都不输出

   > **B**。`for ... else` 的 `else` 仅在循环**正常结束**（未被 `break`）时执行；这里 `i == 3` 时 `break`，所以不打印 `done`。

6. 依次执行以下代码，输出是什么？

   ```python
   class Animal:
       def __init__(self, name):
           self.name = name

       def speak(self):
           print("...")

   class Dog(Animal):
       def speak(self):
           print(f"{self.name}: woof")

   d = Dog("Rex")
   d.speak()
   ```

   - A. `...`
   - B. `Rex: woof`
   - C. 输出两行：`...` 和 `Rex: woof`
   - D. `AttributeError: 'Dog' object has no attribute '__init__'`

   > **B**。`Dog` 没有定义 `__init__`，直接继承 `Animal.__init__` 完成 `self.name = "Rex"`；`speak` 被子类重写，只打印子类版本。

7. 以下代码中，`d` 的值是什么？

   ```python
   d = {"a": 1, "b": 2}
   d = {k: v for k, v in d.items() if v > 1}
   print(d)
   ```

   - A. `{'a': 1, 'b': 2}`
   - B. `{'b': 2}`
   - C. `{1: 'a', 2: 'b'}`
   - D. `SyntaxError: invalid syntax`

   > **B**。字典推导式筛掉了 `v > 1` 不成立的 `a: 1`。

8. 依次执行以下代码，输出是什么？

   ```python
   import json
   s = json.dumps({"name": "张三", "age": 18})
   print(type(s))
   ```

   - A. `<class 'dict'>`
   - B. `<class 'str'>`
   - C. `<class 'bytes'>`
   - D. `TypeError: dump() missing 1 required positional argument: 'fp'`

   > **B**。`dumps` 的 s 是 **s**tring，序列化结果返回字符串；写入文件的 `dump` 才需要 `fp`。

9. 依次执行以下代码，输出是什么？

   ```python
   def f(x):
       return x + 1

   f(5)
   print(f(5))
   ```

   - A. 输出两行：`None` 和 `6`
   - B. 只输出 `6`
   - C. 只输出 `None`
   - D. 输出 `6` 两次

   > **B**。第一行 `f(5)` 有返回值但没被打印、也没被接收，直接被丢弃；只有 `print(f(5))` 输出 `6`。

10. 以下代码中，`user.get("city")` 和 `user["city"]` 的区别是什么？

    ```python
    user = {"name": "张三", "age": 18}
    ```

    - A. 没有区别，两者行为完全一致
    - B. `get()` 返回默认值 `None`，`[]` 抛出 `KeyError`
    - C. `get()` 抛出 `KeyError`，`[]` 返回 `None`
    - D. `get()` 只能用于字符串键，`[]` 可以用于任意键

    > **B**。`dict.get(key)` 键不存在时返回 `None`（可传第二参数自定义默认值）；下标访问 `d[key]` 键不存在直接抛 `KeyError`。

### 答案

```
1. B  2. B  3. B  4. B  5. B  6. B  7. B  8. B  9. B  10. B
```

> 以上每题结论均以 `python` 3.11 **实际执行代码**的输出为准核对过（不是凭记忆）。

---

## 二、简答题（每题 10 分，共 3 题，满分 30 分）

> 说明：直接在本文件对应题目下方作答，支持代码块。

### 第 1 题：浅拷贝与深拷贝

以下代码中，`a`、`b`、`c` 三者之间的关系是什么？执行 `a[0].append(99)` 后，`b` 和 `c` 分别变成什么？请解释原因。

```python
a = [[1, 2], [3, 4]]
b = a.copy()
import copy
c = copy.deepcopy(a)
```

**答：**

三者的关系：

| 对象 | 与外层 `a` 的关系 | 与内层 `[1, 2]` 的关系 |
| --- | --- | --- |
| `b = a.copy()` | **新**的外层列表 | 内层元素仍是**同一个**子列表对象（`b[0] is a[0]` → `True`） |
| `c = copy.deepcopy(a)` | **新**的外层列表 | 内层元素也是**递归复制**出来的新对象（`c[0] is a[0]` → `False`） |

即：`a.copy()` 是**浅拷贝**——只复制最外层容器，元素本身的引用被原样带入；`copy.deepcopy()` 是**深拷贝**——沿着嵌套结构逐层复制，直到所有可变对象都是全新的。

执行 `a[0].append(99)` 之后：

```python
a  →  [[1, 2, 99], [3, 4]]
b  →  [[1, 2, 99], [3, 4]]   # 变了
c  →  [[1, 2], [3, 4]]       # 没变
```

**原因：** `a[0].append(99)` 改动的不是外层列表，而是**内层那个子列表对象本身**。

- `b` 是浅拷贝，它的 `b[0]` 和 `a[0]` 指向同一个列表对象，所以通过 `a` 改动该对象时 `b` 也"跟着变"——这不是 `b` 被改了，而是 `a`、`b` 看到的是同一个东西。
- `c` 是深拷贝，`c[0]` 是独立副本，与 `a[0]` 再无关联，因此不受影响。

补充一个容易混淆的对照：如果是 `a.append([5, 6])`（追加到**外层**），那么 `b` 和 `c` **都不会**变——因为浅拷贝的外层已经是新列表了，改动外层不影响它。浅拷贝的"坑"只发生在往里层可变对象写入时。

实测验证：

```python
>>> import copy
>>> a = [[1, 2], [3, 4]]
>>> b = a.copy(); c = copy.deepcopy(a)
>>> a[0].append(99)
>>> a, b, c
([[1, 2, 99], [3, 4]], [[1, 2, 99], [3, 4]], [[1, 2], [3, 4]])
```

### 第 2 题：字典与列表的综合应用

以下代码模拟"从日志中提取用户信息"，请回答：

```python
logs = [
    {"user": "张三", "action": "login", "level": "INFO"},
    {"user": "李四", "action": "logout", "level": "INFO"},
    {"user": "张三", "action": "error", "level": "ERROR"},
    {"user": "王五", "action": "login", "level": "INFO"},
    {"user": "李四", "action": "error", "level": "ERROR"},
]
```

**1. 写出表达式，找出所有 `level` 为 `"ERROR"` 的日志（返回字典列表）。**

```python
errors = [log for log in logs if log["level"] == "ERROR"]
# [{'user': '张三', 'action': 'error', 'level': 'ERROR'},
#  {'user': '李四', 'action': 'error', 'level': 'ERROR'}]
```

（等价的 `filter` 写法：`list(filter(lambda log: log["level"] == "ERROR", logs))`）

**2. 写出表达式，统计每个用户出现了几次（返回字典，键为用户名，值为次数）。**

```python
from collections import Counter

counts = dict(Counter(log["user"] for log in logs))
# {'张三': 2, '李四': 2, '王五': 1}
```

不用 `collections` 的纯手工写法（等价）：

```python
counts = {}
for log in logs:
    user = log["user"]
    counts[user] = counts.get(user, 0) + 1
# {'张三': 2, '李四': 2, '王五': 1}
```

字典推导式写法（自带去重，只对每个用户算一次）：

```python
counts = {u: sum(1 for log in logs if log["user"] == u) for u in {log["user"] for log in logs}}
```

**3. 解释为什么第 2 问不能直接用 `len(logs)` 得到结果，需要什么遍历结构？**

因为 `len(logs)` 得到的是**日志的总条数**（这里是 5），而第 2 问要的是**按 `user` 字段分组后的计数**——即"同一个用户在列表中出现了几次"。

维度不同：`len` 数的是"元素个数"，题目要的是"按某个键分组后每组的元素个数"。一条日志只贡献 1 给总数，但要贡献 1 给"它所属的那个用户名"这一桶，所以必须**先按 `user` 分组**再计数。

需要的遍历结构是**哈希表（字典）做累加器**：以 `user` 的取值为键、出现次数为值，边遍历边 `+= 1`：

```python
counts = {}
for log in logs:
    key = log["user"]        # 用哪个字段做分组维度
    counts[key] = counts.get(key, 0) + 1   # 字典累积（哈希计数）
```

即「一次线性遍历 + 一个字典」，时间复杂度 O(n)。`collections.Counter` 本质上就是这个字典累加器的封装，专门用来做这件事，所以更推荐直接用它。

**实测结果：**

```python
>>> errors  → [{'user': '张三', 'action': 'error', 'level': 'ERROR'}, {'user': '李四', 'action': 'error', 'level': 'ERROR'}]
>>> counts  → {'张三': 2, '李四': 2, '王五': 1}
>>> len(logs) → 5
```

### 第 3 题：异常处理设计

Day_10 中你写过 `safe_int(s)` 函数：能转就返回整数，不能转就返回 `None`。

现在请你设计一个 `safe_divide(a, b)` 函数：

- 输入两个字符串 `a` 和 `b`
- 尝试将它们转为数字并计算 `a / b`
- 如果转换失败（`ValueError`）或除数为零（`ZeroDivisionError`），返回 `None`
- 否则返回商（`float`）

请写出函数代码，并说明：为什么这里用 `try/except` 比先用 `if` 判断再计算更好？

**答：**

```python
def safe_divide(a: str, b: str) -> float | None:
    """把两个字符串转成数字后相除。

    转换失败（ValueError）或除数为零（ZeroDivisionError）时返回 None，
    否则返回商（float）。
    """
    try:
        return float(a) / float(b)
    except (ValueError, ZeroDivisionError):
        return None
```

验证：

```python
>>> safe_divide("10", "4")     # 2.5
>>> safe_divide("10", "0")     # None  （ZeroDivisionError）
>>> safe_divide("abc", "2")    # None  （ValueError）
>>> safe_divide("1e3", "4")    # 250.0 （科学计数法也是合法 float）
>>> safe_divide("inf", "2")    # inf   （'inf' 对 float() 是合法输入）
```

**为什么 `try/except` 比"先用 `if` 判断再计算"更好？**

1. **"什么样的字符串能转成数字"这件事的标准答案，就是 `float()` 本身。** 用 `if` 去判断，等于手写一个解析器去模拟它，必须穷举：空串、正负号、小数点、多个小数点、`+.5`、`.5`、`5.`、科学计数法 `1e3`/`1E-2`、首尾空格（`float(" 1 ")` 合法）、`inf`/`nan`、下划线分隔（`1_000` 合法）、全角数字……漏掉任何一条就是 bug。而 `float()` 永远与你运行的 Python 版本保持一致的语义，是唯一权威。

2. **除零的判断同样容易漏。** `b` 转出来可能是 `0`、`0.0`、`-0.0`，还可能是 `float("0e5")`；`if b == 0` 这类判断很容易写漏（例如先判断了字符串再判断零，顺序一乱就错）。`try` 里一条语句同时覆盖"转换失败"和"除零"两类异常，`if` 版本要写两处分支 + 两处返回。

3. **EAFP 比 LBYL 更贴合 Python 的风格。** Python 官方术语叫 EAFP（Easier to Ask Forgiveness than Permission，先做、出错再处理）对 LBYL（Look Before You Leap，先检查再动手）。LBYL 还有一个固有的竞态问题：检查与执行之间存在时间窗口，状态可能已经改变——虽然在纯计算里不明显，但这个习惯延续到文件、网络、数据库操作时就会变成真 bug。

4. **正常路径零开销。** 不抛异常时 `try` 几乎不产生额外成本；异常只在对失败路径上付代价。而 `if` 判断每次调用都要多跑一遍判断逻辑，并且让函数体更长。

5. **区分"预期内的失败"和"真 bug"。** 这里 `ValueError` / `ZeroDivisionError` 是题目定义的**预期失败**，用 `except (ValueError, ZeroDivisionError)` 精确捕获并返回 `None`；其他异常（比如传进来不可转的对象导致 `TypeError`）不吞掉，仍会正常抛出，避免把真错误伪装成 `None` 掩盖问题。

> 补充：如果题目要求的是**整数**除法（`int(a) // int(b)`），`int()` 不接受 `"1.5"`、`"inf"` 等，语义又不同——这恰恰说明"转换规则"由你所选的内置函数定义，用 `try/except` 包住它，是唯一不会写错的做法。
