from own_exceptions import InvalidNonce, UnsignedTransaction, InvalidNonce, InsufficientBalance, InvalidTransaction, UncategorizedTransaction, InvalidCategory


null_address = b'\xff' * 20


def rp(tx, what, actual, target):
    return '%r: %r actual:%r target:%r' % (tx, what, actual, target)


def validate_transaction(state, tx):
    # (1) The transaction signature is valid;
    if not tx.sender:  # sender is set and validated on Transaction initialization
        raise UnsignedTransaction(tx)

    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);
    req_nonce = 0 if tx.sender == null_address else state.get_nonce(tx.sender)
    if req_nonce != tx.nonce:
        raise InvalidNonce(rp(tx, 'nonce', tx.nonce, req_nonce))

    # (3) the sender account balance contains the value
    if hasattr(tx, 'category'):
        category = tx.category
        if category < 0 or category > 3:
            raise InvalidCategory(tx)
        balance = state.get_balance(tx.sender)
        value = tx.ip_network
        if category == 1 or category == 2:
            if not balance.in_own_ips(value):
                raise InsufficientBalance(value)
        elif category == 3:
            balance.delegated_ips
            #MapServer
        elif category == 4:
            balance.delegated_ips
            #Locator
    else:
        raise UncategorizedTransaction(tx)

    return True
