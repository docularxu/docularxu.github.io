const fs = require('fs');
const path = require('path');

// Step 1: Read File
const filePath = path.join(__dirname, 'fry-1000.txt');
const fileContent = fs.readFileSync(filePath, 'utf8');

// Step 2: Process Data
// Split by lines, spaces, or tabs, then trim and filter out empty strings
const wordsArray = fileContent.split(/[\n\s\t]+/).map(word => word.trim()).filter(word => word);

// You can also add further data cleansing steps here as needed

// Step 3: Write JS File
const outputFilePath = path.join(__dirname, 'fry-1000-wordsArray.js');
const outputFileContent = `export const wordsArray = ${JSON.stringify(wordsArray)};`;
fs.writeFileSync(outputFilePath, outputFileContent);

console.log('Words array successfully written to wordsArray.js');
