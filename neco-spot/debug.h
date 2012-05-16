#ifndef _DEBUG_H_
#define _DEBUG_H_

#include <iostream>

#ifdef NECO_TRACE

template< typename T >
void __neco__debug__printf__(T msg) {
    std::cout << msg << std::endl;
}

template< typename T1, typename T2 >
void __neco__debug__printf__(T1 msg1, T2 msg2) {
    std::cout << msg1 << " " << msg2 << std::endl;
}

#define NECO_DEBUG_TRACE(msg) __neco__debug__printf__(msg)
#define NECO_DEBUG_TRACE2(msg, msg2) __neco__debug__printf__(msg, msg2)
#else
    #define NECO_DEBUG_TRACE(loc, ...)
    #define NECO_DEBUG_TRACE2(loc, ...)
#endif

#endif /* _DEBUG_H_ */
