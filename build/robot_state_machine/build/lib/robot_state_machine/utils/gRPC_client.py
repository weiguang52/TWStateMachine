import os
import time
import grpc
import itertools

import media_stream_pb2
import media_stream_pb2_grpc


def atomic_write_bytes(final_path: str, data: bytes):
    tmp_path = final_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, final_path)  # 原子替换（同一文件系统内）


def request_stream(session_id="sess-1", robot_id="robot-1"):
    """
    由于是双向流，客户端必须发点东西。
    这里发一个“空音频 + end_of_stream=False”当作 keepalive。
    你也可以改成真实音频分片。
    """
    request_id = "req-1"
    for i in itertools.count():
        yield media_stream_pb2.AudioRequest(
            session_id=session_id,
            robot_id=robot_id,
            request_id=request_id,
            ts=int(time.time() * 1000),
            codec=media_stream_pb2.PCM16,
            sample_rate=16000,
            channels=1,
            audio_chunk=b"",
            end_of_stream=False,
            meta={"client": "save-action-only"}
        )
        time.sleep(1.0)


def run(server_addr="127.0.0.1:50051", out_dir="./actions", max_files=None):
    os.makedirs(out_dir, exist_ok=True)

    with grpc.insecure_channel(server_addr) as channel:
        stub = media_stream_pb2_grpc.VoiceAgentStub(channel)

        idx = 0
        responses = stub.StreamSession(request_stream())

        for resp in responses:
            # 只要 ACTION 的 action_npz
            if resp.type == media_stream_pb2.ACTION and resp.action_npz:
                filename = f"action_{idx:06d}.npz"
                path = os.path.join(out_dir, filename)
                atomic_write_bytes(path, resp.action_npz)
                print(f"[client] saved {path} ({len(resp.action_npz)} bytes) desc={resp.action_description}")
                idx += 1

                if max_files is not None and idx >= max_files:
                    print("[client] reached max_files, exiting.")
                    break

            if resp.end_of_response:
                # server 说这次响应结束（按你协议含义）
                # 如果你希望不断运行，可忽略这个字段或自行定义逻辑
                pass


if __name__ == "__main__":
    run()
