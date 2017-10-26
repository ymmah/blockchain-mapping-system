from own_exceptions import InvalidNonce, UnsignedTransaction, InvalidNonce, InsufficientBalance, InvalidTransaction, UncategorizedTransaction, InvalidCategory


null_address = b'\xff' * 20


def rp(tx, what, actual, target):
    return '%r: %r actual:%r target:%r' % (tx, what, actual, target)


def validate_transaction(state, tx):
    # (1) The transaction signature is valid;
    if not tx.sender:  # sender is set and validated on Transaction initialization
        raise UnsignedTransaction(tx)
    else:
        if tx.sender == null_address:
            raise UnsignedTransaction(tx)
    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);

    req_nonce = state.get_nonce(tx.sender)
    if req_nonce != tx.nonce:
        raise InvalidNonce(rp(tx, 'nonce', tx.nonce, req_nonce))

    # (3) the sender account balance contains the value
    if hasattr(tx, 'category'):
        category = tx.category

        if category < 0 or category > 3:
            raise InvalidCategory(category)

        balance = state.get_balance(tx.sender)
        value = tx.ip_network

        if category == 1 or category == 2:
            if not balance.in_own_ips(value):
                raise InsufficientBalance(value)
        elif category == 3:
            pass
            #MapServer
        elif category == 4:
            pass
            #Locator
    else:
        raise UncategorizedTransaction(tx)

    return True


def apply_transaction(state, tx):

    validate_transaction(state, tx)
    category = tx.category

    if category == 0:  # allocate
        sender = tx.sender
        to = tx.to
        value = tx.ip_network

        sender_balance = state.get_balance(sender)

        affected = sender_balance.affected_delegated_ips(value)
        for add, ips in affected.iteritems():
            sender_balance.remove_delegated_ips(add, ips)
            received_balance = state.get_balance(add)
            received_balance.remove_received_ips(sender, ips)
            state.set_balance(add, received_balance)

        to_balance = state.get_balance(to)
        sender_balance.remove_own_ips(value)
        to_balance.add_own_ips(value)

        state.set_balance(to, to_balance)
        state.set_balance(sender, sender_balance)
        state.increment_nonce(sender)

    elif category == 1:  # delegate
        sender = tx.sender
        to = tx.to
        value = tx.ip_network

        sender_balance = state.get_balance(sender)

        affected = sender_balance.affected_delegated_ips(value)
        for add, ips in affected.iteritems():
            sender_balance.remove_delegated_ips(add, ips)
            received_balance = state.get_balance(add)
            received_balance.remove_received_ips(sender, ips)
            state.set_balance(add, received_balance)

        to_balance = state.get_balance(to)
        to_balance.add_received_ips(sender, value)
        sender_balance.add_delegated_ips(to, value)

        state.set_balance(to, to_balance)
        state.set_balance(sender, sender_balance)
        state.increment_nonce(sender)

    elif category == 2:  # MapServer
        sender = tx.sender
        value = tx.metadata

        sender_balance = state.get_balance(sender)
        sender_balance.set_map_server(value)
        state.set_balance(sender, sender_balance)

    elif category == 3:  # Locator
        sender = tx.sender
        value = tx.metadata

        sender_balance = state.get_balance(sender)
        sender_balance.set_locator(value)
        state.set_balance(sender, sender_balance)

    state.commit()

    return True