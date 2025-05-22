.["@graph"][] | {
  "@id": .["@id"],
  "@type": .["@type"],
  "weight": (
    if .["sys:heuristicWeight"] then 
      .["sys:heuristicWeight"] 
    else 
      (. | tostring | length) 
    end
  ),
  "evictPriority": (
    if .["sys:evictAfter"] then 
      .["sys:evictAfter"] 
    else 
      999
    end
  )
}