# Personal Finance Tracker

A comprehensive Python desktop application for managing personal finances with data visualization and reporting capabilities.

## Features

- **Transaction Management**: Add, view, and categorize income and expenses
- **Data Visualization**: Interactive charts and graphs for financial analysis
- **Database Integration**: SQLite database for persistent data storage
- **Export Functionality**: Export data to CSV format
- **Financial Summary**: Real-time calculation of income, expenses, and net balance
- **User-Friendly GUI**: Built with Tkinter for cross-platform compatibility

## Technologies Used

- **Python 3.x**: Core programming language
- **Tkinter**: GUI framework for desktop application
- **SQLite**: Lightweight database for data persistence
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualization and plotting
- **Datetime**: Date and time handling

## Installation

1. Clone or download the project files
2. Install required dependencies:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
python finance_tracker.py
```

## Usage

### Adding Transactions
1. Go to the "Add Transaction" tab
2. Fill in the transaction details:
   - Date (YYYY-MM-DD format)
   - Type (Income or Expense)
   - Category (automatically populated based on type)
   - Description (optional)
   - Amount
3. Click "Add Transaction" to save

### Viewing Transactions
1. Go to the "View Transactions" tab
2. Use filters to view specific transaction types
3. Export data using the "Export to CSV" button

### Financial Analytics
1. Go to the "Analytics" tab
2. Click "Update Summary" to see:
   - Total Income
   - Total Expenses
   - Net Balance (color-coded: green for positive, red for negative)

## Project Structure

```
personal-finance-tracker/
│
├── finance_tracker.py      # Main application file
├── requirements.txt        # Project dependencies
├── README.md              # Project documentation
├── finance_tracker.db     # SQLite database (created automatically)
└── sample_data.py         # Sample data generator (optional)
```

## Database Schema

### Transactions Table
- `id`: Primary key (auto-increment)
- `date`: Transaction date (TEXT)
- `type`: Income or Expense (TEXT)
- `category`: Transaction category (TEXT)
- `description`: Optional description (TEXT)
- `amount`: Transaction amount (REAL)
- `created_at`: Timestamp (TIMESTAMP)

### Budgets Table
- `id`: Primary key (auto-increment)
- `category`: Budget category (TEXT)
- `monthly_limit`: Monthly spending limit (REAL)
- `created_at`: Timestamp (TIMESTAMP)

## Key Learning Outcomes

This project demonstrates proficiency in:

- **GUI Development**: Creating user-friendly interfaces with Tkinter
- **Database Operations**: CRUD operations with SQLite
- **Data Analysis**: Processing and analyzing financial data with Pandas
- **Data Visualization**: Creating charts and graphs with Matplotlib
- **Software Architecture**: Organizing code using object-oriented programming
- **Error Handling**: Implementing robust error handling and user feedback
- **File I/O**: Reading from and writing to various file formats

## Future Enhancements

- Budget tracking and alerts
- Recurring transaction support
- Multiple account management
- Advanced reporting features
- Data import from bank statements
- Cloud synchronization
- Mobile app integration

## Screenshots

[Note: Add screenshots of the application interface here]

## Contributing

This is a learning project. Feel free to fork and modify for your own use.

## License

This project is open source and available under the MIT License.

## Contact

[Your Name]
[Your Email]
[Your GitHub Profile]
