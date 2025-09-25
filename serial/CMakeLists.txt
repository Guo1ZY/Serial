file(GLOB_RECURSE serial_srcs CONFIGURE_DEPENDS include/*.hpp sources/*.cpp)

add_library(serial STATIC ${serial_srcs})

add_thread(serial)

target_include_directories(serial PUBLIC include)
