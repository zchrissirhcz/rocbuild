# https://www.cnblogs.com/zjutzz/p/18198833
if(MSVC)
  target_link_options(your_target PRIVATE "/STACK:10485760") # 10 MB stack size
endif()
