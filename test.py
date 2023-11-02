import datetime
# 獲取當前的本地時間
local_time = datetime.datetime.now()

# 獲取昨天的日期
date = (datetime.datetime.now() -
        datetime.timedelta(days=1)).strftime('%Y-%m-%d')

print(date)
