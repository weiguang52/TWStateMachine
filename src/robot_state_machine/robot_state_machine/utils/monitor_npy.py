import os
import time
import numpy as np

def watch_npy_empty(
    path: str = "/tmp/robot_action.npy",
    interval: float = 0.2,
    on_change=None,
    treat_all_nan_as_empty: bool = True,
):
    """
    监视 npy 文件是否为空（或不可用），当状态变化时触发回调。

    空的判定（按顺序）：
      1) 文件不存在 -> 空
      2) 文件大小为 0 -> 空
      3) np.load 失败（写入中/损坏/未完成）-> 视为空（继续等）
      4) 读出来是空数组（size==0）-> 空
      5) 可选：数组全部为 NaN -> 空

    参数:
      path: 监视路径
      interval: 轮询间隔（秒）
      on_change: 回调函数，签名 on_change(is_empty: bool, info: dict)
      treat_all_nan_as_empty: 是否把“全 NaN”当作空

    返回:
      None（该函数会一直阻塞运行，直到被 Ctrl+C 或外部结束）
    """
    last_state = None

    while True:
        info = {"path": path}
        is_empty = True

        try:
            st = os.stat(path)  # 不存在会抛异常
            info["size_bytes"] = st.st_size
            info["mtime"] = st.st_mtime

            if st.st_size == 0:
                is_empty = True
                info["reason"] = "size=0"
            else:
                try:
                    arr = np.load(path, allow_pickle=False)
                    info["shape"] = getattr(arr, "shape", None)
                    info["dtype"] = getattr(arr, "dtype", None)

                    if not hasattr(arr, "size") or arr.size == 0:
                        is_empty = True
                        info["reason"] = "array.size==0"
                    elif treat_all_nan_as_empty and np.issubdtype(arr.dtype, np.floating) and np.isnan(arr).all():
                        is_empty = True
                        info["reason"] = "all_nan"
                    else:
                        is_empty = False
                        info["reason"] = "ok"
                except Exception as e:
                    # 常见情况：写入过程中读到半截、文件尚未写完等
                    is_empty = True
                    info["reason"] = "load_error"
                    info["error"] = repr(e)

        except FileNotFoundError:
            is_empty = True
            info["reason"] = "not_found"
        except Exception as e:
            is_empty = True
            info["reason"] = "stat_error"
            info["error"] = repr(e)

        # 状态变化才通知
        if last_state is None or is_empty != last_state:
            last_state = is_empty
            if on_change:
                on_change(is_empty, info)
            else:
                print(f"[watch] empty={is_empty} info={info}")

        time.sleep(interval)


# 示例用法：
if __name__ == "__main__":
    def cb(is_empty, info):
        print(f"EMPTY={is_empty} reason={info.get('reason')} size={info.get('size_bytes')} shape={info.get('shape')}")

    watch_npy_empty("/tmp/robot_action.npy", interval=0.2, on_change=cb)