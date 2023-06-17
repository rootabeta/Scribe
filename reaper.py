import sqlite3 

#select sum(influence), avg(daysSinceLogin) from cache where region='greater_sahara' and strftime('%s', 'now') - 1209600 > daysSinceLogin
secondsSince = 25 * 24 * 60 * 60

print(secondsSince)
