from datetime import datetime, timezone
from typing import Optional, Dict, List
import uuid

# GST Rates Configuration
GST_RATES = {
    'Visa': 0.18,
    'Ticket': 0.05,
    'Package': 0.05,
    'Other': 0.18
}

# Chart of Accounts - Master Categories
ACCOUNT_TYPES = {
    'Assets': ['Cash', 'Bank - Current Account', 'Bank - Savings Account', 'Accounts Receivable'],
    'Liabilities': ['Accounts Payable', 'GST Payable - CGST', 'GST Payable - SGST', 'GST Payable - IGST'],
    'Income': ['Visa Revenue', 'Ticket Revenue', 'Tour Package Revenue', 'Other Income'],
    'Expenses': ['Office Rent', 'Staff Salaries', 'Marketing', 'Utilities', 'Travel Expenses', 'Miscellaneous']
}

class AccountingService:
    def __init__(self, db):
        self.db = db
    
    async def initialize_accounts(self):
        """Initialize chart of accounts if not exists"""
        existing = await self.db.accounts.count_documents({})
        if existing > 0:
            return
        
        accounts = []
        for account_type, account_names in ACCOUNT_TYPES.items():
            for name in account_names:
                accounts.append({
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'type': account_type,
                    'code': f"{account_type[:3].upper()}-{len(accounts)+1:04d}",
                    'balance': 0.0,
                    'created_at': datetime.now(timezone.utc).isoformat()
                })
        
        if accounts:
            await self.db.accounts.insert_many(accounts)
    
    def calculate_gst(self, amount: float, source: str) -> Dict[str, float]:
        """Calculate GST breakdown for a transaction"""
        gst_rate = GST_RATES.get(source, 0.18)
        
        # Calculate taxable amount (amount is inclusive of GST)
        taxable_amount = amount / (1 + gst_rate)
        total_gst = amount - taxable_amount
        
        # Split CGST and SGST (equal for intra-state)
        cgst = total_gst / 2
        sgst = total_gst / 2
        
        return {
            'taxable_amount': round(taxable_amount, 2),
            'cgst': round(cgst, 2),
            'sgst': round(sgst, 2),
            'igst': 0.0,  # For inter-state, would be total_gst
            'total_gst': round(total_gst, 2),
            'gst_rate': gst_rate * 100
        }
    
    async def create_revenue_ledger_entry(self, revenue_data: dict):
        """Create double-entry ledger for revenue transaction"""
        amount = revenue_data['received_amount']
        if amount <= 0:
            return
        
        source = revenue_data['source']
        gst_breakdown = self.calculate_gst(amount, source)
        
        # Create ledger entries
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        ledger_entries = [
            # Debit: Cash/Bank (Asset increases)
            {
                'id': str(uuid.uuid4()),
                'entry_id': entry_id,
                'date': revenue_data['date'],
                'account': 'Cash' if revenue_data['payment_mode'] == 'Cash' else 'Bank - Current Account',
                'account_type': 'Assets',
                'debit': amount,
                'credit': 0.0,
                'description': f"Revenue from {source} - {revenue_data['client_name']}",
                'reference_type': 'revenue',
                'reference_id': revenue_data['id'],
                'created_at': timestamp
            },
            # Credit: Revenue Account (Income increases)
            {
                'id': str(uuid.uuid4()),
                'entry_id': entry_id,
                'date': revenue_data['date'],
                'account': f"{source} Revenue",
                'account_type': 'Income',
                'debit': 0.0,
                'credit': gst_breakdown['taxable_amount'],
                'description': f"Revenue from {source} - {revenue_data['client_name']}",
                'reference_type': 'revenue',
                'reference_id': revenue_data['id'],
                'created_at': timestamp
            },
            # Credit: GST Payable - CGST
            {
                'id': str(uuid.uuid4()),
                'entry_id': entry_id,
                'date': revenue_data['date'],
                'account': 'GST Payable - CGST',
                'account_type': 'Liabilities',
                'debit': 0.0,
                'credit': gst_breakdown['cgst'],
                'description': f"CGST @ {gst_breakdown['gst_rate']/2}% on {source}",
                'reference_type': 'revenue',
                'reference_id': revenue_data['id'],
                'created_at': timestamp
            },
            # Credit: GST Payable - SGST
            {
                'id': str(uuid.uuid4()),
                'entry_id': entry_id,
                'date': revenue_data['date'],
                'account': 'GST Payable - SGST',
                'account_type': 'Liabilities',
                'debit': 0.0,
                'credit': gst_breakdown['sgst'],
                'description': f"SGST @ {gst_breakdown['gst_rate']/2}% on {source}",
                'reference_type': 'revenue',
                'reference_id': revenue_data['id'],
                'created_at': timestamp
            }
        ]
        
        await self.db.ledgers.insert_many(ledger_entries)
        
        # Store GST record
        gst_record = {
            'id': str(uuid.uuid4()),
            'date': revenue_data['date'],
            'type': 'output',  # Output GST (sales)
            'invoice_number': f"INV-{revenue_data['id'][:8].upper()}",
            'client_name': revenue_data['client_name'],
            'gstin': '',  # Client GSTIN if available
            'service_type': source,
            'taxable_amount': gst_breakdown['taxable_amount'],
            'cgst': gst_breakdown['cgst'],
            'sgst': gst_breakdown['sgst'],
            'igst': gst_breakdown['igst'],
            'total_gst': gst_breakdown['total_gst'],
            'total_amount': amount,
            'gst_rate': gst_breakdown['gst_rate'],
            'reference_id': revenue_data['id'],
            'created_at': timestamp
        }
        
        await self.db.gst_records.insert_one(gst_record)
        
        # Update account balances
        await self.update_account_balance('Cash' if revenue_data['payment_mode'] == 'Cash' else 'Bank - Current Account', amount, 'debit')
        await self.update_account_balance(f"{source} Revenue", gst_breakdown['taxable_amount'], 'credit')
        await self.update_account_balance('GST Payable - CGST', gst_breakdown['cgst'], 'credit')
        await self.update_account_balance('GST Payable - SGST', gst_breakdown['sgst'], 'credit')
    
    async def create_expense_ledger_entry(self, expense_data: dict):
        """Create double-entry ledger for expense transaction"""
        amount = expense_data['amount']
        
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        ledger_entries = [
            # Debit: Expense Account (Expense increases)
            {
                'id': str(uuid.uuid4()),
                'entry_id': entry_id,
                'date': expense_data['date'],
                'account': expense_data['category'],
                'account_type': 'Expenses',
                'debit': amount,
                'credit': 0.0,
                'description': expense_data.get('description', f"Expense for {expense_data['category']}"),
                'reference_type': 'expense',
                'reference_id': expense_data['id'],
                'created_at': timestamp
            },
            # Credit: Cash/Bank (Asset decreases)
            {
                'id': str(uuid.uuid4()),
                'entry_id': entry_id,
                'date': expense_data['date'],
                'account': 'Cash' if expense_data['payment_mode'] == 'Cash' else 'Bank - Current Account',
                'account_type': 'Assets',
                'debit': 0.0,
                'credit': amount,
                'description': expense_data.get('description', f"Expense for {expense_data['category']}"),
                'reference_type': 'expense',
                'reference_id': expense_data['id'],
                'created_at': timestamp
            }
        ]
        
        await self.db.ledgers.insert_many(ledger_entries)
        
        # Update account balances
        await self.update_account_balance(expense_data['category'], amount, 'debit')
        await self.update_account_balance('Cash' if expense_data['payment_mode'] == 'Cash' else 'Bank - Current Account', amount, 'credit')
    
    async def update_account_balance(self, account_name: str, amount: float, type: str):
        """Update account balance"""
        account = await self.db.accounts.find_one({'name': account_name})
        if not account:
            # Create account if doesn't exist
            account_type = 'Expenses' if type == 'debit' else 'Income'
            account = {
                'id': str(uuid.uuid4()),
                'name': account_name,
                'type': account_type,
                'code': f"{account_type[:3].upper()}-{await self.db.accounts.count_documents({})+1:04d}",
                'balance': 0.0,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await self.db.accounts.insert_one(account)
        
        current_balance = account.get('balance', 0.0)
        if type == 'debit':
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
        
        await self.db.accounts.update_one(
            {'name': account_name},
            {'$set': {'balance': new_balance}}
        )
    
    async def update_revenue_ledger_entry(self, revenue_id: str, old_amount: float, new_amount: float, revenue_data: dict):
        """Update existing revenue ledger entries with difference-based approach"""
        
        # Calculate difference
        amount_diff = new_amount - old_amount
        
        if amount_diff == 0:
            return  # No change needed
        
        # Update ledger entries by applying the difference
        ledger_entries = await self.db.ledgers.find({'reference_id': revenue_id}).to_list(100)
        
        for entry in ledger_entries:
            old_debit = entry.get('debit', 0.0)
            old_credit = entry.get('credit', 0.0)
            
            # Calculate proportional change
            if old_debit > 0:
                new_debit = old_debit + (amount_diff * old_debit / old_amount)
                await self.db.ledgers.update_one(
                    {'id': entry['id']},
                    {'$set': {'debit': new_debit}}
                )
                # Update account balance with difference
                account_name = entry['account']
                await self.update_account_balance(account_name, amount_diff * old_debit / old_amount, 'debit')
            
            if old_credit > 0:
                new_credit = old_credit + (amount_diff * old_credit / old_amount)
                await self.db.ledgers.update_one(
                    {'id': entry['id']},
                    {'$set': {'credit': new_credit}}
                )
                # Update account balance with difference
                account_name = entry['account']
                await self.update_account_balance(account_name, amount_diff * old_credit / old_amount, 'credit')
        
        # Update GST records if they exist
        gst_records = await self.db.gst_records.find({'reference_id': revenue_id}).to_list(100)
        if gst_records:
            # Recalculate GST with new amount
            source = revenue_data.get('source', 'Other')
            gst_breakdown = self.calculate_gst(new_amount, source)
            
            for gst_record in gst_records:
                await self.db.gst_records.update_one(
                    {'id': gst_record['id']},
                    {'$set': {
                        'taxable_amount': gst_breakdown['taxable_amount'],
                        'cgst': gst_breakdown['cgst'],
                        'sgst': gst_breakdown['sgst'],
                        'total_gst': gst_breakdown['total_gst'],
                        'total_amount': new_amount
                    }}
                )
    
    async def update_expense_ledger_entry(self, expense_id: str, old_amount: float, new_amount: float, expense_data: dict):
        """Update existing expense ledger entries with difference-based approach"""
        
        # Calculate difference
        amount_diff = new_amount - old_amount
        
        if amount_diff == 0:
            return  # No change needed
        
        # Update ledger entries by applying the difference
        ledger_entries = await self.db.ledgers.find({'reference_id': expense_id}).to_list(100)
        
        for entry in ledger_entries:
            old_debit = entry.get('debit', 0.0)
            old_credit = entry.get('credit', 0.0)
            
            # Update amounts proportionally
            if old_debit > 0:
                new_debit = old_debit + amount_diff
                await self.db.ledgers.update_one(
                    {'id': entry['id']},
                    {'$set': {'debit': new_debit}}
                )
                # Update account balance with difference
                account_name = entry['account']
                await self.update_account_balance(account_name, amount_diff, 'debit')
            
            if old_credit > 0:
                new_credit = old_credit + amount_diff
                await self.db.ledgers.update_one(
                    {'id': entry['id']},
                    {'$set': {'credit': new_credit}}
                )
                # Update account balance with difference
                account_name = entry['account']
                await self.update_account_balance(account_name, amount_diff, 'credit')
        
        # Update GST records for Purchase for Resale
        if expense_data.get('purchase_type') == 'Purchase for Resale' and expense_data.get('gst_rate', 0) > 0:
            gst_records = await self.db.gst_records.find({'reference_id': expense_id}).to_list(100)
            
            # Recalculate GST amounts
            gst_rate = expense_data.get('gst_rate', 18) / 100
            taxable_amount = new_amount / (1 + gst_rate)
            cgst = (taxable_amount * gst_rate) / 2
            sgst = (taxable_amount * gst_rate) / 2
            
            for gst_record in gst_records:
                await self.db.gst_records.update_one(
                    {'id': gst_record['id']},
                    {'$set': {
                        'taxable_amount': taxable_amount,
                        'cgst': cgst,
                        'sgst': sgst,
                        'total_gst': cgst + sgst,
                        'total_amount': new_amount
                    }}
                )
    
    async def get_trial_balance(self):
        """Generate trial balance"""
        accounts = await self.db.accounts.find({}, {'_id': 0}).to_list(1000)
        
        trial_balance = []
        total_debit = 0.0
        total_credit = 0.0
        
        for account in accounts:
            balance = account.get('balance', 0.0)
            account_type = account['type']
            
            # Determine if balance is debit or credit based on account type
            if account_type in ['Assets', 'Expenses']:
                debit = abs(balance)
                credit = 0.0
                total_debit += debit
            else:  # Liabilities, Income
                debit = 0.0
                credit = abs(balance)
                total_credit += credit
            
            trial_balance.append({
                'account_name': account['name'],
                'account_code': account['code'],
                'account_type': account_type,
                'debit': round(debit, 2),
                'credit': round(credit, 2),
                'balance': round(balance, 2)
            })
        
        return {
            'accounts': trial_balance,
            'total_debit': round(total_debit, 2),
            'total_credit': round(total_credit, 2),
            'balanced': abs(total_debit - total_credit) < 0.01
        }
    
    async def get_gst_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Generate GST summary report"""
        query = {}
        if start_date and end_date:
            query['date'] = {'$gte': start_date, '$lte': end_date}
        
        gst_records = await self.db.gst_records.find(query, {'_id': 0}).to_list(1000)
        
        output_gst = {'cgst': 0, 'sgst': 0, 'igst': 0, 'total': 0}
        input_gst = {'cgst': 0, 'sgst': 0, 'igst': 0, 'total': 0}
        
        for record in gst_records:
            if record['type'] == 'output':
                output_gst['cgst'] += record['cgst']
                output_gst['sgst'] += record['sgst']
                output_gst['igst'] += record['igst']
                output_gst['total'] += record['total_gst']
            elif record['type'] == 'input':
                input_gst['cgst'] += record['cgst']
                input_gst['sgst'] += record['sgst']
                input_gst['igst'] += record['igst']
                input_gst['total'] += record['total_gst']
        
        net_payable = output_gst['total'] - input_gst['total']
        
        return {
            'output_gst': {
                'cgst': round(output_gst['cgst'], 2),
                'sgst': round(output_gst['sgst'], 2),
                'igst': round(output_gst['igst'], 2),
                'total': round(output_gst['total'], 2)
            },
            'input_gst': {
                'cgst': round(input_gst['cgst'], 2),
                'sgst': round(input_gst['sgst'], 2),
                'igst': round(input_gst['igst'], 2),
                'total': round(input_gst['total'], 2)
            },
            'net_gst_payable': round(net_payable, 2),
            'records': gst_records
        }
    
    async def create_input_gst_record(self, expense_data: dict):
        """Create GST input record for purchases"""
        amount = expense_data['amount']
        gst_rate = expense_data.get('gst_rate', 0) / 100
        
        # Calculate GST breakdown
        taxable_amount = amount / (1 + gst_rate)
        total_gst = amount - taxable_amount
        cgst = total_gst / 2
        sgst = total_gst / 2
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        gst_record = {
            'id': str(uuid.uuid4()),
            'date': expense_data['date'],
            'type': 'input',  # Input GST (purchases)
            'invoice_number': expense_data.get('invoice_number', ''),
            'supplier_gstin': expense_data.get('supplier_gstin', ''),
            'category': expense_data['category'],
            'taxable_amount': round(taxable_amount, 2),
            'cgst': round(cgst, 2),
            'sgst': round(sgst, 2),
            'igst': 0.0,
            'total_gst': round(total_gst, 2),
            'total_amount': amount,
            'gst_rate': expense_data.get('gst_rate', 0),
            'reference_id': expense_data['id'],
            'created_at': timestamp
        }
        
        await self.db.gst_records.insert_one(gst_record)


    async def create_vendor_payment_ledger_entries(self, revenue_id: str, cost_detail: dict, vendor_payments: List[Dict]):
        """
        Create ledger entries for vendor partial payments
        Each payment creates:
        - Debit: Vendor - [Vendor Name] (Liability decrease)
        - Credit: Bank/Cash (Asset decrease)
        """
        vendor_name = cost_detail.get('vendor_name', 'Unknown Vendor')
        
        for payment in vendor_payments:
            payment_id = payment.get('id', str(uuid.uuid4()))
            amount = payment.get('amount', 0)
            payment_date = payment.get('date')
            payment_mode = payment.get('payment_mode', 'Bank Transfer')
            
            if amount <= 0:
                continue
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Determine payment account based on mode
            payment_account = 'Cash' if payment_mode == 'Cash' else 'Bank - Current Account'
            
            # Create vendor ledger entry (Debit - decreasing liability)
            vendor_ledger = {
                'id': str(uuid.uuid4()),
                'date': payment_date,
                'account': f"Vendor - {vendor_name}",
                'description': f"Payment to vendor via {payment_mode}",
                'debit': amount,
                'credit': 0.0,
                'reference_type': 'vendor_payment',
                'reference_id': f"{revenue_id}_{cost_detail.get('id')}_{payment_id}",
                'created_at': timestamp
            }
            
            # Create bank/cash ledger entry (Credit - decreasing asset)
            payment_ledger = {
                'id': str(uuid.uuid4()),
                'date': payment_date,
                'account': payment_account,
                'description': f"Payment to {vendor_name} via {payment_mode}",
                'debit': 0.0,
                'credit': amount,
                'reference_type': 'vendor_payment',
                'reference_id': f"{revenue_id}_{cost_detail.get('id')}_{payment_id}",
                'created_at': timestamp
            }
            
            # Insert both ledger entries
            await self.db.ledgers.insert_many([vendor_ledger, payment_ledger])
            
            # Update account balances
            await self.update_account_balance(f"Vendor - {vendor_name}", amount, 'debit')
            await self.update_account_balance(payment_account, amount, 'credit')
    
    async def delete_vendor_payment_ledger_entries(self, revenue_id: str, cost_detail_id: str):
        """Delete all vendor payment ledger entries for a specific cost detail"""
        # Find all ledger entries with reference starting with revenue_id and cost_detail_id
        reference_prefix = f"{revenue_id}_{cost_detail_id}"
        
        ledger_entries = await self.db.ledgers.find({
            'reference_type': 'vendor_payment',
            'reference_id': {'$regex': f'^{reference_prefix}'}
        }).to_list(1000)
        
        # Reverse each entry (opposite operation to restore balance)
        for entry in ledger_entries:
            account = entry['account']
            debit_amount = entry.get('debit', 0)
            credit_amount = entry.get('credit', 0)
            
            # Reverse the balance change
            if debit_amount > 0:
                await self.update_account_balance(account, debit_amount, 'credit')
            if credit_amount > 0:
                await self.update_account_balance(account, credit_amount, 'debit')
        
        # Delete the ledger entries
        await self.db.ledgers.delete_many({
            'reference_type': 'vendor_payment',
            'reference_id': {'$regex': f'^{reference_prefix}'}
        })

