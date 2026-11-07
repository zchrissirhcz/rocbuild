cmake_minimum_required(VERSION 3.20)
project(atomic_demo)

add_executable(${PROJECT_NAME} demo.cpp)

# ---------------------------------------------------------------------------
# 通用规则:GCC/Clang 上,当 std::atomic<T> 不满足 lock-free 时,编译器会
# 把原子操作降级为对 libatomic 的外部函数调用,必须显式链接 -latomic。
#
#   - std::atomic<T> 是否 lock-free 由 is_always_lock_free 决定;
#     若不满足,则 store/load/exchange/fetch_* 等操作会生成
#     __atomic_load / __atomic_store / __atomic_exchange 等外部符号。
#   - 常见的不 lock-free 情形:类型过大、对不齐、或架构本身缺少
#     对应的单指令原子原语(如 32 位 x86 上的 8 字节操作、某些 ARM 上的
#     多字节操作),都会走 libatomic。
#   - 这类符号只在链接期解析,漏链接会报 undefined reference。
#   - MSVC 无此问题:其 _InterlockedXxx 由 CRT 内建提供,无需额外库。
#
# 具体到本例:demo.cpp 使用 std::atomic<MyStruct>,而 MyStruct 由
#   int + double + long long 组成,经对齐后为 24 字节,超过单条原子
#   指令能覆盖的范围(典型为 8 字节;16 字节需 cmpxchg16b 且要求对齐),
#   因此 is_always_lock_free == false,store/load/exchange 全部外联到
#   libatomic。故这里必须为 GNU/Clang 家族链接 atomic。
#
# 验证方法:编译后在目标文件上执行
#     nm -C demo.cpp.o | grep __atomic_
#   应能看到 U __atomic_load / U __atomic_store / U __atomic_exchange
#   这类未定义符号,即证明依赖 libatomic。
#
# 备注:若希望彻底摆脱 libatomic 依赖,可考虑:
#   1) 改用 std::atomic<MyStruct*>,原子化指针而非大对象;
#   2) 用 std::mutex 保护 24 字节对象,语义等价且可移植;
#   3) 拆成多个 lock-free 的 std::atomic 字段(但会失去整体一致性,
#      需另配 seqlock / 版本号等机制)。
# ---------------------------------------------------------------------------
target_link_libraries(${PROJECT_NAME}
  PRIVATE
    $<$<IN_LIST:$<CXX_COMPILER_ID>,GNU;Clang>:atomic>
)
