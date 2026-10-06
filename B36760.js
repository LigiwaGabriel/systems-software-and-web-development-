/*
 CAMPUS CANTEEN BILLING SYSTEM

 Description:
 This program simulates a simple billing system for a campus canteen.
 The cashier chooses items from a menu, enters quantities, and the
 program calculates the subtotal, applies a discount (if the customer
 qualifies), accepts payment, calculates change, and prints a receipt.

 How to run:
 1. Open a terminal.
 2. Navigate to the folder containing this file.
 3. Run: node B36760.js

 How to use:
 1. A menu of items and prices (in UGX) is displayed.
 2. Type the number of an item and press Enter.
 3. Type the quantity you want and press Enter.
 4. Repeat for more items. Type 0 when the order is complete.
 5. The program shows the bill. Enter the amount paid by the customer.
 6. If the money is not enough, the program asks again.
 7. A receipt with the change is printed at the end.
*/

const readline = require("readline");

// Set up the readline interface so we can read input from the console
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

// The canteen menu: each item has a name and a price in UGX
const menu = [
  { name: "Rolex", price: 3000 },
  { name: "Chapati", price: 1000 },
  { name: "Samosa", price: 1500 },
  { name: "Chicken & Chips", price: 12000 },
  { name: "Soda", price: 2000 },
  { name: "Mineral Water", price: 1500 },
];

/*
 Helper: asks the user a question and waits for the answer.
 Wrapping rl.question in a Promise lets us use "await" in the main
 program so the code reads from top to bottom.
*/
function ask(question) {
  return new Promise((resolve) => rl.question(question, resolve));
}

/*
 FUNCTION 1: displayMenu
 Prints all menu items with their numbers and prices.
 Uses a FOR loop to go through the menu array.
*/
function displayMenu() {
  console.log("\n========== CANTEEN MENU ==========");
  for (let i = 0; i < menu.length; i++) {
    console.log(`${i + 1}. ${menu[i].name} - UGX ${menu[i].price}`);
  }
  console.log("0. Finish order and pay");
  console.log("==================================");
}

/*
 FUNCTION 2: calculateSubtotal
 Adds up (price x quantity) for every item in the order.
 Uses a FOR...OF loop to go through the order.
*/
function calculateSubtotal(order) {
  let subtotal = 0;
  for (const line of order) {
    subtotal += line.price * line.quantity;
  }
  return subtotal;
}

/*
 FUNCTION 3: calculateDiscount
 Decides the discount rate using if / else if / else:
   - UGX 50,000 or more  -> 10% discount
   - UGX 20,000 or more  -> 5% discount
   - Otherwise           -> no discount
 Returns the discount amount in UGX.
*/
function calculateDiscount(subtotal) {
  if (subtotal >= 50000) {
    return subtotal * 0.1;
  } else if (subtotal >= 20000) {
    return subtotal * 0.05;
  } else {
    return 0;
  }
}

/*
 FUNCTION 4: printReceipt
 Prints a neat receipt showing every item, the totals, the amount
 paid and the change given.
*/
function printReceipt(order, subtotal, discount, total, paid) {
  console.log("\n============== RECEIPT ==============");
  for (const line of order) {
    const lineTotal = line.price * line.quantity;
    console.log(`${line.name} x${line.quantity}  =  UGX ${lineTotal}`);
  }
  console.log("-------------------------------------");
  console.log(`Subtotal : UGX ${subtotal}`);
  console.log(`Discount : UGX ${discount}`);
  console.log(`TOTAL    : UGX ${total}`);
  console.log(`Paid     : UGX ${paid}`);
  console.log(`Change   : UGX ${paid - total}`);
  console.log("=====================================");
  console.log("Thank you for eating with us!\n");
}

/*
 MAIN PROGRAM
 Controls the flow: take the order, calculate the bill, take payment.
*/
async function main() {
  console.log("Welcome to the Campus Canteen Billing System!");

  const order = []; // stores the items the customer has chosen
  let choosing = true;

  // LOOP: keep asking for items until the cashier types 0
  while (choosing) {
    displayMenu();
    const choice = parseInt(await ask("Enter item number: "));

    if (choice === 0) {
      // Do not allow payment on an empty order
      if (order.length === 0) {
        console.log("Your order is empty. Please choose at least one item.");
      } else {
        choosing = false;
      }
    } else if (isNaN(choice) || choice < 1 || choice > menu.length) {
      // Invalid input: not a number or not on the menu
      console.log("Invalid choice. Please pick a number from the menu.");
    } else {
      const item = menu[choice - 1];
      const quantity = parseInt(await ask(`How many ${item.name}? `));

      if (isNaN(quantity) || quantity < 1) {
        console.log("Invalid quantity. Item not added.");
      } else {
        order.push({ name: item.name, price: item.price, quantity: quantity });
        console.log(`Added ${quantity} x ${item.name}.`);
      }
    }
  }

  // Calculate the bill using our functions
  const subtotal = calculateSubtotal(order);
  const discount = calculateDiscount(subtotal);
  const total = subtotal - discount;

  console.log(`\nSubtotal: UGX ${subtotal}`);
  if (discount > 0) {
    console.log(`You qualify for a discount of UGX ${discount}!`);
  } else {
    console.log("No discount on this order (spend UGX 20,000+ to get one).");
  }
  console.log(`Amount to pay: UGX ${total}`);

  // LOOP: keep asking for payment until the customer pays enough
  let paid = 0;
  while (paid < total) {
    paid = parseFloat(await ask("Enter amount paid (UGX): "));
    if (isNaN(paid) || paid < total) {
      console.log("Not enough money or invalid amount. Try again.");
      paid = 0;
    }
  }

  printReceipt(order, subtotal, discount, total, paid);
  rl.close();
}

main();