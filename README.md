## Pseudocode Interpreter

To build locally, run:

```bash
yarn
cd editor
yarn
yarn build
```

To start pseudocode interpreter websocket, run:

```bash
pip install -r requirements.txt
python webserver.py
```
Then websocket is ready at `ws://127.0.0.1:5000/`


To test pseudocode interpreter:

```bash
cd editor
python cambridgeScript input.p
```
