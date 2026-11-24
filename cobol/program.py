#!/usr/bin/env python3
"""
Re-implementation of the COBOL program BOOKFORUM in Python.
Reads from src/INPUT.DAT and updates data/ACCOUNTS.DAT, data/BOOKS.DAT, data/TRANSACTIONS.DAT
as per the COBOL logic. Designed to be run from the cobol/ directory.
"""

import os
from pathlib import Path

# Record lengths based on COBOL PICs
ACCOUNT_LEN = 4 + 20 + 10  # 34
BOOK_LEN = 4 + 20 + 4      # 28
TRANS_LEN = 4 + 10 + 4 + 4 # 22
INPUT_LEN = 4 + 4 + 4 + 10 # 22

def read_fixed_records(filepath, record_len):
    """Read a sequential fixed-length record file into a list of byte strings."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'rb') as f:
        data = f.read()
    records = []
    for i in range(0, len(data), record_len):
        rec = data[i:i+record_len]
        if len(rec) < record_len:
            # Pad short records with spaces (common COBOL behavior for incomplete)
            rec = rec.ljust(record_len, b' ')
        records.append(rec)
    return records

def write_fixed_records(filepath, records):
    """Write list of fixed-length records back to file (no separators)."""
    with open(filepath, 'wb') as f:
        for rec in records:
            f.write(rec)

def main():
    base = Path('.')
    input_path = base / 'src' / 'INPUT.DAT'
    accounts_path = base / 'data' / 'ACCOUNTS.DAT'
    books_path = base / 'data' / 'BOOKS.DAT'
    trans_path = base / 'data' / 'TRANSACTIONS.DAT'

    # Read input (one record)
    if not input_path.exists() or input_path.stat().st_size == 0:
        print("Error: Input file is empty")
        return

    with open(input_path, 'rb') as f:
        input_data = f.read(INPUT_LEN)
    if len(input_data) < INPUT_LEN:
        input_data = input_data.ljust(INPUT_LEN, b' ')

    buyer_id = input_data[0:4].decode('ascii', errors='replace').strip()
    seller_id = input_data[4:8].decode('ascii', errors='replace').strip()
    book_id = input_data[8:12].decode('ascii', errors='replace').strip()
    amount_str = input_data[12:22].decode('ascii', errors='replace').strip()

    try:
        # Treat amount as integer for balance (decimals zero); pad and parse
        amount = int(amount_str) if amount_str.isdigit() else 0
    except ValueError:
        amount = 0

    # Validation
    accounts = read_fixed_records(accounts_path, ACCOUNT_LEN)
    books = read_fixed_records(books_path, BOOK_LEN)

    buyer_found = False
    seller_found = False
    book_found = False
    valid_owner = False

    for rec in accounts:
        acc_id = rec[0:4].decode('ascii').strip()
        if acc_id == buyer_id:
            buyer_found = True
        if acc_id == seller_id:
            seller_found = True

    for rec in books:
        b_id = rec[0:4].decode('ascii').strip()
        owner = rec[24:28].decode('ascii').strip()
        if b_id == book_id:
            book_found = True
            if owner == seller_id:
                valid_owner = True

    print(" ")  # as in COBOL DISPLAY " ".

    if buyer_found and seller_found and book_found and valid_owner:
        # Process transaction
        # Update accounts
        new_accounts = []
        for rec in accounts:
            acc_id = rec[0:4].decode('ascii').strip()
            name = rec[4:24]
            bal_str = rec[24:34].decode('ascii')
            balance = int(bal_str) if bal_str.isdigit() else 0
            if acc_id == buyer_id:
                balance -= amount
            if acc_id == seller_id:
                balance += amount
            # Ensure non-negative? COBOL doesn't check, but keep as is
            new_bal = f"{balance:010d}"[-10:]  # 10 digits, truncate if needed
            new_rec = rec[0:4] + name + new_bal.encode('ascii')
            new_accounts.append(new_rec)
        write_fixed_records(accounts_path, new_accounts)

        # Update books
        new_books = []
        for rec in books:
            b_id = rec[0:4].decode('ascii').strip()
            if b_id == book_id:
                # Change owner to buyer
                new_rec = rec[0:24] + buyer_id.ljust(4).encode('ascii')
            else:
                new_rec = rec
            new_books.append(new_rec)
        write_fixed_records(books_path, new_books)

        # Append transaction
        # TRANS-BOOK (4) + TRANS-AMOUNT (10) + TRANS-SELLER (4) + TRANS-BUYER (4)
        amount_field = f"{amount:010d}"
        trans_rec = (
            book_id.ljust(4).encode('ascii') +
            amount_field.encode('ascii') +
            seller_id.ljust(4).encode('ascii') +
            buyer_id.ljust(4).encode('ascii')
        )
        with open(trans_path, 'ab') as f:
            f.write(trans_rec)

        print("Transaction completed successfully")
    else:
        print("Transaction failed due to validation errors")

if __name__ == '__main__':
    main()
