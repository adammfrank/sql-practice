SELECT id
FROM products
WHERE attributes @> '{"color":"red","size":"m"}';
