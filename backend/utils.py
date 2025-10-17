from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from websocket import create_connection  
import json
from datetime import datetime
from hashlib import sha256
import uvicorn

class Transaction():
    def __init__(self,origin:str,content:object) -> None:
        self._origin:str = origin
        self._timestamp = str(datetime.now())
        self._content = content

class Block():
    def __init__(self):
        self._transactions:list[Transaction] = []
        
        def hasher(transactions:list[Transaction]):
            transactions = [data.__dict__ for data in transactions]
            json_string = json.dumps(transactions) 
            utf8_bytes = json_string.encode("utf-8")
            return sha256(utf8_bytes).hexdigest()
        
        self.currhash:str =  hasher(self._transactions)
        self.prevhash:str = None
        self._timstamp:datetime = datetime.now()
    def addTransaction(self,transaction:Transaction):
        self._transactions.append(transaction)
    

class Blockchain():
    def __init__(self) -> None:
        self._block_list:list[Block] = []
        self.latest_block_hash  = None
        self.curr_block = Block()
    def addBlock(self,block:Block):
        self._block_list.append(block)
        self._latest_block_hash = block.currhash

class Peer(Blockchain):
    def __init__(self,location:str,port:int,peers:list[str]) -> None:
        super(Peer,self).__init__()
        self.location = location
        self.peers:list[str] = peers
        self.port = port
        self._app = FastAPI()

        @self._app.websocket(f"/ws/{self.location}")
        async def websocket_endpoint(websocket: WebSocket):
                await websocket.accept()
                try:
                    while True:
                            data = await websocket.receive_json()
                            if data:
                                if data['type'] == 'broadcast':
                                    print(f"I recieved this {data}")
                                    # await websocket.send_text("Recieved")
                                else:
                                    print("I got this")
                                    data['type'] = 'broadcast'
                                    for peer_uri in self.peers:
                                        ws = create_connection(peer_uri) 
                                        ws.send(json.dumps(data))
                                        # info = ws.recv()
                                        ws.close()
                except WebSocketDisconnect:
                    print("Succesfull Transmission")
    def run(self):
        uvicorn.run(self._app,port=self.port)