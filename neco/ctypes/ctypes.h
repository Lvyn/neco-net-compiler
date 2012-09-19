#ifndef _CTYPES_H_
#define _CTYPES_H_

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <utility>
#include <iostream>

#define INT_INIT_MAX_SIZE 2
#define INT_RESIZE 4

/////////////////////////////////////////////////////
// int place type
/////////////////////////////////////////////////////

//#ifndef NDEBUG
#define ASSERT(condition, msg) \
	assert(condition && msg); \
	std::cerr << msg << std::endl; \
	exit(-1);

/*#else
#define ASSERT(condition, msg)
#endif
*/

// used by qsort
inline int int_cmp(const void* a, const void* b) {
    return *(int*)a - *(int*)b;
}

inline unsigned int int_hash(int a) {
    unsigned int hash = a;
    hash = hash ^ (hash>>4);
    hash = (hash^0xdeadbeef) + (hash<<5);
    hash = hash ^ (hash>>11);
    return hash;
}

template <typename T>
struct THashProvider
{
	static int hash(const T& value) {
		ASSERT(0, "no suitable specialization (HashProvider)");
		return 0;
	}
};

template <>
struct THashProvider<int>
{
	inline static int hash(int value) {
		return value;
	}
};

template <typename T>
struct TDefaultComparisonProvider
{
	inline static int compare(T& left, T& right) {
		ASSERT(0, "no suitable specialization (DefaultComparisonProvider)");
		return 0;
	}
};

template <typename T>
struct TDefaultComparisonProvider<T*>
{
	inline static int compare(T* left, T* right) {
		ASSERT(0, "no suitable specialization (Ptr DefaultComparisonProvider)");
		return 0;
	}
};

template <typename T>
struct TFormatter
{
	inline static size_t format(char* buffer, const T& value) {
		ASSERT(0, "no suitable specialization (TFormatter)");
		return 0;
	}
};


template <>
struct TDefaultComparisonProvider<int>
{
	typedef int T;
	inline static int compare(T& left, T& right) {
		return left - right;
	}
};


template <typename T>
struct TDefaultDataTypeHandler
{
	typedef TDefaultComparisonProvider<T> ComparisonProvider;
	typedef THashProvider<T> HashProvider;
	typedef TFormatter<T> Formatter;
};

// T is assumed to be a POD type
template< typename DataType,
		   template <typename> class DataTypeHandler = TDefaultDataTypeHandler >
class TGenericPlaceType {
	typedef typename DataTypeHandler<DataType>::ComparisonProvider ComparisonProvider;
	typedef typename DataTypeHandler<DataType>::HashProvider HashProvider;
	typedef typename DataTypeHandler<DataType>::Formatter Formatter;

public:
	TGenericPlaceType():
			mRefs(1),
			mSize(0),
			mMaxSize(INT_INIT_MAX_SIZE),
			mData(new DataType[ INT_INIT_MAX_SIZE ]) {
	}

	TGenericPlaceType(const TGenericPlaceType& src):
			mRefs(1),
			mSize(src.mSize),
			mMaxSize(src.mMaxSize),
			mData(new DataType[ src.mMaxSize ]) {

		memcpy(mData, src.mData, src.mSize * sizeof(DataType));
	}


	~TGenericPlaceType() {
		delete[] mData;
	}

	void clean() {
		assert(0);
		mSize = 0;
	}

	inline void decrement_ref() {
		mRefs--;
		if (mRefs == 0)
			delete this;
	}

	inline void increment_ref() {
		mRefs++;
	}

	inline bool not_empty() const { return mSize > 0; }

	char* cstr() const {
		static char s_buf[1024];

	    // TO DO accept bigger strings
	    char tmp[20];
	    int i, size;

	    s_buf[0] = '\0';
	    strcpy(s_buf, "[");
	    size = this->size();
	    for (i = size-1; i >= 0; i--) {
	    	std::cout << "FORMAT !" << std::endl;
			Formatter::format(tmp, mData[i]);
			if (i > 0)
				strcat(tmp, ", ");
			strcat(s_buf, tmp);
	    }
	    strcat(s_buf, "]");
	    return s_buf;
	}

    int equals(const TGenericPlaceType<DataType>& right) const {
        int i;
        int tmp;

        if (this == &right)
         	return 1;

        tmp = mSize - right.mSize;
        if (tmp != 0)
        	return 0; // tmp;

        //////////////////////////////////////////////////
        // ENSURE ORDERED !!!
        //////////////////////////////////////////////////

        for (i = mSize-1; i >= 0; i--) {
        	tmp = ComparisonProvider::compare( mData[i], right.mData[i] );
        	if (tmp != 0)
        		return 0;
        }
        return 1;
    }


    int compare(const TGenericPlaceType<DataType>& right) const {
        int i;
        int tmp;
        int this_size;

        if (this == &right)
         	return 0;

        this_size = size();
        tmp = this_size - right.size();
        if (tmp != 0)
        	return tmp;

        //////////////////////////////////////////////////
        // ENSURE ORDERED !!!
        //////////////////////////////////////////////////

        for (i = this_size-1; i >= 0; i--) {
    		tmp = ComparisonProvider::compare( mData[i], right.mData[i] );
    		if (tmp != 0)
    			return tmp;
        }
        return 0;
    }


    int hash() const {
        int i = mSize - 1;
        int hash = 0; // int_hash(pt->size);
        for (; i >= 0; i--) {
        	hash ^= hash << 5;
        	hash = (hash ^ HashProvider::hash(mData[i]));
        }
        return hash;
    }

    void add(DataType value) {
        int i, j;
        if (mSize >= mMaxSize) {
    		mMaxSize += INT_RESIZE;
    		DataType *new_data = new DataType[mMaxSize];
    		for (int i = 0; i < mSize; ++i) {
    			new_data[i] = mData[i];
    		}
    		delete mData;
    		mData = new_data;
        }
        // find suitable index
        for (i = 0; i < mSize; i++) {
    	if (ComparisonProvider::compare(mData[i], value) < 0)
    	    continue;
    	else
    	    break;
        }

        // shift values
        for (j = mSize+1; j > i; j--) {
        	mData[j] = mData[j-1];
        }

        // store new value
        mData[i] = value;
        mSize++;
    }


    inline void remove_by_index(int index) {
        mSize--;
        for (int i = index; i < mSize; i++)
         	mData[i] = mData[i+1];
    }

    void remove_by_value(DataType value) {
        int index = 0;
        for (; index < mSize; index++) {
    		if (mData[index] == value) {
    			mSize--;
    			mData[index] = mData[mSize];
    			break;
    		}
        }
        qsort(mData, mSize, sizeof(int), int_cmp);
    }

    inline DataType& get(int index) { return mData[index]; }

    inline int size() const { return mSize; }

    void update(const TGenericPlaceType& right) {
        assert(0);
    }

    int index_of(const DataType& value) const {
    	for (int i = 0; i < mSize; ++i) {
    		if (mData[i] == value) {
    			return i;
    		}
    	}
    	return -1;
    }

protected:
    int mRefs;
	int mSize;
	int mMaxSize;
	DataType *mData;
};


template< typename T >
class TPid
{
public:
	TPid() {}

	TPid(int i) {
		mData.push_back(i);
	}

	TPid(const TPid<T>& pid) {
		for (size_t i = 0; i < pid.mData.size(); ++i) {
			mData.push_back(pid.mData[i]);
		}
	}

	TPid(const TPid<T>& pid, int next) {
		for (size_t i = 0; i < pid.mData.size(); ++i) {
			mData.push_back(pid.mData[i]);
		}
		mData.push_back(next);
	}

	~TPid() {}

	bool operator == (const TPid<T>& right) {
		for (size_t i = 0; i < right.mData.size(); ++i) {
			if (mData[i] != right.mData[i])
				return false;
		}
		return true;
	}

	int compare(const TPid<T>& right) {
		for (size_t i = 0; i < right.mData.size(); ++i) {
			int cmp = mData[i] - right.mData[i];
			if (cmp != 0) {
				return cmp;
			}
		}
		return 0;
	}

	size_t format(char* buffer) {
		size_t offset = 0;
		for (size_t i = 0; i < mData.size(); ++i) {
			if (i > 0) {
				offset += sprintf(buffer + offset, ".");
			}
			offset += sprintf(buffer + offset, "%d", mData[i]);
		}
		*(buffer + offset) = '\0';
		std::cout << "BUFFER !!! " << buffer << std::endl;
		return offset;
	}

private:
	std::vector<T> mData;
};

template < typename T1, typename T2 >
class Pair
{
	typedef Pair<T1, T2> ThisType;
public:
	Pair()
	{}

	Pair(const T1& v1, const T2& v2):
		mFst(v1), mSnd(v2)
	{}

	Pair(const ThisType& pair):
		mFst(pair.mFst), mSnd(pair.mSnd)
	{}

	void set_first(const T1& v) { mFst = v; }
	void set_second(const T2& v) { mSnd = v; }

	T1 get_first() const { return mFst; }
	T2 get_second() const { return mSnd; }

private:
	T1 mFst;
	T2 mSnd;
};

template< typename PidType, typename CounterType,
		   template <typename> class ComparisonProvider = TDefaultComparisonProvider >
class TGeneratorPlaceType: public TGenericPlaceType< Pair<PidType, CounterType>, ComparisonProvider >
{
	typedef Pair<PidType, CounterType> DataType;
	typedef TGeneratorPlaceType<PidType, CounterType, ComparisonProvider> ThisType;
	typedef TGenericPlaceType< Pair<PidType, CounterType>, ComparisonProvider > BaseType;
public:
	TGeneratorPlaceType()
	{}
	TGeneratorPlaceType(const ThisType& other):
		TGenericPlaceType< DataType >(other)
	{}

	void update_pid_counter(const PidType& pid, CounterType counter) {
		for (int i = 0; i < this->mSize; ++i) {
			DataType& current = this->mData[i];
			int cmp = ComparisonProvider<PidType>::compare(current.get_first(), pid);
			if (cmp == 0) {
				current.set_second(counter);
				this->mData[i] = current;
				return;

			} else if (cmp > 0) {
				break;
			}
		}
		// not updated, new pid
		add( Pair<PidType, CounterType>(pid, counter) );
	}

	void remove_pid(const PidType& pid) {
		for (int i = 0; i < this->mSize; ++i) {
			DataType& current = this->mData[i];
			int cmp = ComparisonProvider<PidType>::compare(current.get_first(), pid);
			if (cmp == 0) {
				BaseType::remove_by_index(i);
				return;
			} else if (cmp > 0) {
				return;
			}
		}
	}
};


template <>
struct TFormatter<int>
{
	inline static size_t format(char* buffer, int value) {
		return sprintf(buffer, "%d", value);
	}
};

template <>
struct TFormatter< TPid<int> >
{
	inline static size_t format(char* buffer, TPid<int>& pid) {
		return pid.format(buffer);
	}
};

template <typename TLeft, typename TRight>
struct TFormatter< Pair< TLeft, TRight > >
{
	inline static size_t format(char* buffer, Pair< TLeft, TRight>& pair) {
		char *initial_buffer = buffer;
		buffer += sprintf(buffer, "<");
		buffer += TFormatter< TLeft >::format(buffer, pair.get_first());
		buffer += sprintf(buffer, ", ");
		buffer += TFormatter< TRight >::format(buffer, pair.get_second());
		buffer += sprintf(buffer, ">");
		return buffer - initial_buffer;
	}
};

//////////////////////////////////////////////////

//static inline void structure_copy(void* dst, void* src, int n) {
//    memcpy(dst, src, n);
//}
//
//static inline int structure_cmp(void* dst, void* src, int n) {
//    return strncmp((char*)dst, (char*)src, n) == 0;
//}
//
//static inline int structure_to_int(void* dst, int i) {
//    return ((int *)dst)[i];
//}
//
//static inline int structure_to_char(void* dst, int i) {
//    return ((char *)dst)[i];
//}

// #define TO_ADDR(x) &(x)

//////////////////////////////////////////////////
// lists with iterators
// needed for SPOT
//////////////////////////////////////////////////

//typedef struct neco_list_node {
//    void *elt;
//    struct neco_list_node* next;
//} neco_list_node_t;
//
//typedef struct neco_list {
//    neco_list_node_t* begin;
//} neco_list_t;
//
//neco_list_t* neco_list_new(void);
//
//int neco_list_length(neco_list_t* list);
//
//void neco_list_push_front(neco_list_t* list, void *elt);
//
//typedef void (*deletion_callback)(void *);
//
//void neco_list_delete(neco_list_t* list, deletion_callback del);

// inline neco_list_node_t* neco_list_first(neco_list_t* list) {
//     return list->begin;
// }

// inline neco_list_node_t* neco_list_node_next(neco_list_node_t* node) {
//     return node->next;
// }

#endif /* _CTYPES_H_ */
