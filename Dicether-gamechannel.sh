echo "analyze Dicether (GameChannel) 0x7e0178e1720e8b3a52086a23187947f35b6f3fc4"

# You can try to change the maxCount to 2000, but it will take a long time to run.

python3 -m smcon.main --address 0x7e0178e1720e8b3a52086a23187947f35b6f3fc4 --maxCount 200  --configuration ./result/0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel-config.json

echo "mine Dicether (GameChannel) automata 0x7e0178e1720e8b3a52086a23187947f35b6f3fc4"
python3 -m smcon.core.ConMiner ./result 0x7e0178e1720e8b3a52086a23187947f35b6f3fc4 GameChannel ./result/0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel-trace.inv.json ./result/0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel-config.json ./result/0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel-trace_slices.json 
