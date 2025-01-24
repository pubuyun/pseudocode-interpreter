import asyncio
import websockets
import json
import subprocess
import os
import time

# 维护一个字典，用于存储每个 WebSocket 客户端的输入和执行状态
clients = {}

async def handle_connection(websocket):
    client_id = id(websocket)
    clients[client_id] = {
        "websocket": websocket,
        "input_text": "",
        "process": None
    }

    try:
        async for message in websocket:
            data = json.loads(message)
            print(data)
            
            if "code" in data:
                code = data["code"]
                
                # 启动代码执行进程
                process = await execute_code(websocket, code, client_id)
                clients[client_id]["process"] = process

                # 开始监听子进程的输出和错误
                asyncio.create_task(read_stdout(websocket, process))
                asyncio.create_task(read_stderr(websocket, process))

            elif "input" in data:
                # 发送输入到子进程
                input_text = data["input"]
                await send_input(clients[client_id]["process"], input_text)

    except websockets.exceptions.ConnectionClosed:
        os.remove(temp_file_path)
    finally:
        # 清理客户端
        process = clients[client_id]["process"]
        if process:
            process.terminate()
        del clients[client_id]

async def execute_code(websocket, code, clientid):
    # 在当前目录下创建一个临时文件来存储代码
    global temp_file_path 
    temp_file_path = f"{clientid}.p"
    print(temp_file_path)
    temp_file = open(temp_file_path, "w")
    temp_file.write(code)
    temp_file.flush()
    temp_file.close()
    print("tempfile saved to", temp_file_path, "code:", code)
    try:
        # 启动子进程
        process = await asyncio.create_subprocess_exec(
            "python", "cambridgeScript", temp_file_path,  # 直接运行创建的文件
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        await websocket.send(json.dumps({"error": f"Failed to start process: {str(e)}"}))
        return None

    return process

async def read_stdout(websocket, process):
    # 逐行读取 stdout，并实时发送到 WebSocket
    try:
        async for line in process.stdout:
            output = line.decode("utf-8").strip()
            print("output:", output)
            await websocket.send(json.dumps({"output": output + "\n"}))
    except Exception as e:
        await websocket.send(json.dumps({"error": f"Error reading stdout: {str(e)}"}))

async def read_stderr(websocket, process):
    # 逐行读取 stderr，并实时发送到 WebSocket
    try:
        async for line in process.stderr:
            error_output = line.decode("utf-8").strip()
            print("error:", error_output)
            await websocket.send(json.dumps({"error": error_output + "\n"}))
    except Exception as e:
        await websocket.send(json.dumps({"error": f"Error reading stderr: {str(e)}"}))

async def send_input(process, input_text):
    if process and process.stdin:
        try:
            process.stdin.write(input_text.encode() + b"\n")
            await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"Error sending input to process: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 5000):
        print("WebSocket server is running on ws://0.0.0.0:5000")
        await asyncio.Future()  # Run forever
        
        

if __name__ == "__main__":
    try:
        asyncio.run(main()) 
    except ProcessLookupError:
        os.remove(temp_file_path)
