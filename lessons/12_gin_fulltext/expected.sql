SELECT id
FROM reviews
WHERE to_tsvector('english', body) @@ plainto_tsquery('english', 'dog');
