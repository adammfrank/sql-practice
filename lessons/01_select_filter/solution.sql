select p.category, SUM(oi.price * oi.quantity )                              
from order_items as oi join products as p on oi.product_id = p.id            
join orders as o on oi.order_id = o.id                                       
where o.status = 'paid'                                                      
group by p.category;                                                         