# Load packages -------------------------------------------------------------------------------
library("RSQLite")
library("tidyverse")

# Handle input --------------------------------------------------------------------------------
args = commandArgs(T)

filename = args[1]

# Anonymize table -----------------------------------------------------------------------------
# filename = "participant.db"
con = dbConnect(SQLite(), dbname = paste0(filename))
tablenames = dbListTables(con)

l.table = list()
for (i in 1:length(tablenames)) {
  l.table[[i]] = dbReadTable(con, tablenames[i])
}
dbDisconnect(con)

l.data = list()
for (i in 1:length(tablenames)) {
  print(i)
  l.data[[i]] = l.table[[i]] %>%
    mutate(
      datastring = str_replace_all(datastring, uniqueid, as.character(row_number())),
      datastring = str_replace_all(datastring, workerid, as.character(row_number()))
    ) %>%
    select(-uniqueid, -workerid, -ipaddress)
}

con = dbConnect(SQLite(), paste0(str_remove(filename, ".db"), "_anonymized.db"))

for (i in 1:length(tablenames)) {
  dbWriteTable(con, tablenames[i], l.data[[i]])
}
dbDisconnect(con)