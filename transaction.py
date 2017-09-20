import cryptography as cr
from ipaddress import IPv4Address

__version__ = '1'   # Must have integer representation

def bytes_to_int(data):
    return int.from_bytes(data, byteorder='little')


def int_to_bytes(integer, length):
    return integer.to_bytes(length=length, byteorder='little')


def hex_to_bytes(data):
    return bytes.fromhex(data)


def ip_to_bytes(addr):
    address, mask = addr.split('/')
    address = int(IPv4Address(address))
    return int_to_bytes(address, 4) + int_to_bytes(int(mask), 1)


def length_to_bytes(n):
    r = b''
    if n < 253:
        length = 1
    elif n <= 0xFFFF:
        length = 2
        r += hex_to_bytes('fd') 
    else:
        length = 4
        r += hex_to_bytes('fe')
    r += int_to_bytes(n, length)
    return r


def make_output(output):
    address, ips = output
    return ip_to_bytes(ips) + hex_to_bytes(cr.address_to_hash160(address))


def get_script(input):
    return hex_to_bytes('0000000000000000')


def get_transaction_id(transaction):
    tx = b''
    input_count = transaction[4]
    tx += transaction[:5]
    if input_count == 0xfd:
        input_count = bytes_to_int(transaction[5:7])
        tx += transaction[5:7]
    elif input_count == 0xfe:
        input_count = bytes_to_int(transaction[5:9])
        tx += transaction[5:9]

    index = len(tx)

    for i in range(input_count):
        tx += transaction[index:index+36]
        index += 36
        script_length = transaction[index]
        index += 1
        if script_length == 0xfd:
            script_length = bytes_to_int(transaction[index:index+3])
            index += 2
        elif script_length == 0xfe:
            script_length = bytes_to_int(transaction[index:index+5])
            index += 4
        index += script_length

    tx += transaction[index:]
    return cr.double_sha256(tx)


def make_transaction(privkeys, inputs, outputs, locktime):
    tx = b''
    tx += int_to_bytes(int(__version__), 4)   # 4 bytes

    tx += length_to_bytes(len(inputs)) # 1+ bytes

    tx_out = b''
    tx_out += length_to_bytes(len(outputs)) # +1 bytes
    tx_out += b''.join(map(make_output, outputs))

    tx_locktime = int_to_bytes(locktime, 4)
    
    prev_scripts = list(map(get_script, inputs))

    pub_keys = list(map(cr.privkey_to_pubkey, privkeys))

    script_sigs = []
    for i, input in enumerate(inputs):
        tx_aux = tx
        for j in range(i):
            tx_aux += hex_to_bytes(inputs[j][0])    \
                    + int_to_bytes(inputs[j][1], 4) \
                    + hex_to_bytes('00')

        tx_aux += hex_to_bytes(input[0])    \
                + int_to_bytes(input[1], 4) \
                + prev_scripts[i]

        for j in range(i+1, len(inputs)):
            tx_aux += hex_to_bytes(inputs[j][0])    \
                    + int_to_bytes(inputs[j][1], 4) \
                    + hex_to_bytes('00')

        tx_aux += tx_out + tx_locktime
        sig = cr.generate_signature(privkeys[i], tx_aux)
        script_sig = int_to_bytes(len(sig), 1) + sig        \
                    + int_to_bytes(len(pub_keys[i])//2, 1)  \
                    + hex_to_bytes(pub_keys[i])
        script_sig = length_to_bytes(len(script_sig)) + script_sig
        script_sigs.append(script_sig)

    tx_in = b''
    for i, input in enumerate(inputs):
        tx_in += hex_to_bytes(input[0])     \
                + int_to_bytes(input[1], 4) \
                + script_sigs[i]

    tx += tx_in + tx_out + tx_locktime
    return tx


def main():
    # TESTS
    privkeys = ['2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c',
               '1cb99b78710454890b32a6207e72b335d55e8222e8ec6af5c416f5daf601bc44',
               '84cd947d91cf4b13b573988f829b2573ff4a15eebb1a39c4288ec45ef7dc0b10']
    
    inputs = [('3110b2c2810b6d3a2c558ba62cc305a4b75ddbda6b0204f44d5cb80564c63852', 0),
              ('d1bd200ecf87320b3f5bb465c7ade141067bc9f1e0623726e1f9a282bb3f3b91', 3),
              ('3b04a3c1a4155f757374b29786f3f7c43273f7638f5d94b8c38fbd3e4888fbb7', 1)]

    outputs = [('16L2y2kkatSZLUWgq11AcH1GmD7vVJk6Jv', '192.152.0.0/16'),
               ('18hqs6eChqSppu5gc39NVHX15PJaHus5zL', '192.160.15.0/30')]

    locktime = 0

    print (make_transaction(privkeys, inputs, outputs, locktime).hex())


if __name__ == "__main__":
    main()