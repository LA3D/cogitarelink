.["@graph"][] | 
if .["@type"] == "Product" then 
  {
    "@id": .["@id"],
    "@type": .["@type"],
    "name": .name,
    "price": .price,
    "productId": .productId,
    "category": .category,
    "specs": .specs
  }
elif .["@type"] == "Review" then
  {
    "@id": .["@id"],
    "@type": .["@type"],
    "author": .author,
    "rating": .rating,
    "reviewDate": .reviewDate,
    "reviewRating": .reviewRating
  }
else
  .
end