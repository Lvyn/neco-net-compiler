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

#ifndef NDEBUG
#define ASSERT(condition, msg) \
	assert(condition && msg); \
	std::cerr << msg << std::endl; \
	exit(-1);

#else
#define ASSERT(condition, msg)
#endif

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
	inline static int 		hash(int value) 				{	return value; }
};

template <typename T>
struct TDefaultComparisonProvider
{
	inline static int 		compare(T& left, T& right) 		{ ASSERT(0, "no suitable specialization (DefaultComparisonProvider)"); return 0; }
};

template <typename T>
struct TDefaultComparisonProvider<T*>
{
	inline static int 		compare(T* left, T* right) 		{ ASSERT(0, "no suitable specialization (Ptr DefaultComparisonProvider)"); return 0; }
};

template <typename T>
struct TFormatter
{
	inline static size_t 	format(char* buffer, const T& value) 	{ ASSERT(0, "no suitable specialization (TFormatter)"); return 0; }
};


template <>
struct TDefaultComparisonProvider<int>
{
	typedef int T;
	inline static int 		compare(T& left, T& right) 		{ return left - right; }
};


template <typename T>
struct TDefaultDataTypeHandler
{
	typedef TDefaultComparisonProvider<T> 		ComparisonProvider_t;
	typedef THashProvider<T> 					HashProvider_t;
	typedef TFormatter<T> 						Formatter_t;
};



#define TGenericPlaceType_TARGS \
template< typename DataType, \
		  template <typename> class DataTypeHandler >

#define TGenericPlaceType_CLS \
TGenericPlaceType<DataType, DataTypeHandler>

// T is assumed to be a POD type
template< typename DataType,
		  template <typename> class DataTypeHandler = TDefaultDataTypeHandler >
class TGenericPlaceType {
	typedef typename DataTypeHandler<DataType>::ComparisonProvider_t 	ComparisonProvider_t;
	typedef typename DataTypeHandler<DataType>::HashProvider_t 			HashProvider_t;
	typedef typename DataTypeHandler<DataType>::Formatter_t 			Formatter_t;

public:
	inline 					TGenericPlaceType();
	inline 					TGenericPlaceType(const TGenericPlaceType& src);
	inline 					~TGenericPlaceType();

	inline void 			decrement_ref();
	inline void 			increment_ref();

    void 					add(DataType value);
    inline void 			remove_by_index(int index);
    void 					remove_by_value(DataType value);
    void 					update(const TGenericPlaceType& right);
    inline void 			clean();

    inline int 				size() const;
	inline bool 			not_empty() const;
    inline const DataType& 	get(int index) const;
    int 					index_of(const DataType& value) const;

    int 					equals(const TGenericPlaceType<DataType>& right) const;
    int 					compare(const TGenericPlaceType<DataType>& right) const;
    int 					hash() const;

    char* 					cstr() const;

protected:
    int 					mRefs;
	int 					mSize;
	int 					mMaxSize;
	DataType*				mData;
};

//

TGenericPlaceType_TARGS
TGenericPlaceType_CLS::TGenericPlaceType()
		: mRefs(1)
		, mSize(0)
		, mMaxSize(INT_INIT_MAX_SIZE)
		, mData(new DataType[ INT_INIT_MAX_SIZE ])
{
}

TGenericPlaceType_TARGS
TGenericPlaceType_CLS::TGenericPlaceType(const TGenericPlaceType& src)
		: mRefs(1)
		, mSize(src.mSize)
		, mMaxSize(src.mMaxSize)
		, mData(new DataType[ src.mMaxSize ])
{
	memcpy(mData, src.mData, src.mSize * sizeof(DataType));
}

TGenericPlaceType_TARGS
TGenericPlaceType_CLS::~TGenericPlaceType()
{
	delete[] mData;
}

TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::clean()
{
	assert(0);
	mSize = 0;
}

TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::decrement_ref()
{
	mRefs--;
	if (mRefs == 0)
		delete this;
}

TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::increment_ref()
{
	mRefs++;
}

TGenericPlaceType_TARGS
bool TGenericPlaceType_CLS::not_empty() const
{
	return mSize > 0;
}

TGenericPlaceType_TARGS
char* TGenericPlaceType_CLS::cstr() const
{
	static char s_buf[1024];

    // TO DO accept bigger strings
    char tmp[20];
    int i, size;

    s_buf[0] = '\0';
    strcpy(s_buf, "[");
    size = this->size();
    for (i = size-1; i >= 0; i--) {
    	Formatter_t::format(tmp, mData[i]);
	if (i > 0) {
		strcat(tmp, ", ");
	}
	strcat(s_buf, tmp);
    }
    strcat(s_buf, "]");
    return s_buf;
}

TGenericPlaceType_TARGS
int TGenericPlaceType_CLS::equals(const TGenericPlaceType<DataType>& right) const
{
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
    	tmp = ComparisonProvider_t::compare( mData[i], right.mData[i] );
    	if (tmp != 0)
    		return 0;
    }
    return 1;
}

TGenericPlaceType_TARGS
int TGenericPlaceType_CLS::compare(const TGenericPlaceType<DataType>& right) const
{
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
		tmp = ComparisonProvider_t::compare( mData[i], right.mData[i] );
		if (tmp != 0)
			return tmp;
    }
    return 0;
}

TGenericPlaceType_TARGS
int TGenericPlaceType_CLS::hash() const
{
    int i = mSize - 1;
    int hash = 0; // int_hash(pt->size);
    for (; i >= 0; i--) {
    	hash ^= hash << 5;
    	hash = (hash ^ HashProvider_t::hash(mData[i]));
    }
    return hash;
}


TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::add(DataType value)
{
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
	if (ComparisonProvider_t::compare(mData[i], value) < 0)
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

TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::remove_by_index(int index)
{
    mSize--;
    for (int i = index; i < mSize; i++)
     	mData[i] = mData[i+1];
}

TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::remove_by_value(DataType value)
{
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

TGenericPlaceType_TARGS
const DataType& TGenericPlaceType_CLS::get(int index) const
{
	return mData[index];
}

TGenericPlaceType_TARGS
int TGenericPlaceType_CLS::size() const
{
	return mSize;
}

TGenericPlaceType_TARGS
void TGenericPlaceType_CLS::update(const TGenericPlaceType& right)
{
    assert(0);
}

TGenericPlaceType_TARGS
int TGenericPlaceType_CLS::index_of(const DataType& value) const
{
	for (int i = 0; i < mSize; ++i) {
		if (mData[i] == value) {
			return i;
		}
	}
	return -1;
}

#undef TGenericPlaceType_TARGS
#undef TGenericPlaceType_CLS


#define TPid_TARGS 		template< typename T >
#define TPid_CLS		TPid<T>

template< typename T >
class TPid
{
public:
	inline				TPid();
	inline				TPid(int i);
	inline				TPid(const TPid<T>& pid);
	inline				TPid(const TPid<T>& pid, int next);
	inline				~TPid();

	inline bool 		operator == (const TPid<T>& right);
	inline int 			compare(const TPid<T>& right);
	inline size_t 		format(char* buffer);

private:
	std::vector<T> 		mData;
};



TPid_TARGS
TPid_CLS::TPid()
{
}

TPid_TARGS
TPid_CLS::TPid(int i)
{
	mData.push_back(i);
}

TPid_TARGS
TPid_CLS::TPid(const TPid<T>& pid)
{
	for (size_t i = 0; i < pid.mData.size(); ++i) {
		mData.push_back(pid.mData[i]);
	}
}

TPid_TARGS
TPid_CLS::TPid(const TPid<T>& pid, int next)
{
	for (size_t i = 0; i < pid.mData.size(); ++i) {
		mData.push_back(pid.mData[i]);
	}
	mData.push_back(next);
}

TPid_TARGS
TPid_CLS::~TPid()
{
}

TPid_TARGS
bool TPid_CLS::operator == (const TPid<T>& right)
{
	for (size_t i = 0; i < right.mData.size(); ++i) {
		if (mData[i] != right.mData[i])
			return false;
	}
	return true;
}

TPid_TARGS
int TPid_CLS::compare(const TPid<T>& right)
{
	for (size_t i = 0; i < right.mData.size(); ++i) {
		int cmp = mData[i] - right.mData[i];
		if (cmp != 0) {
			return cmp;
		}
	}
	return 0;
}

TPid_TARGS
size_t TPid_CLS::format(char* buffer)
{
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

#undef TPid_TARGS
#undef TPid_CLS


#define TGeneratorPlaceType_TARGS \
template< typename PidType, typename CounterType, template <typename> class ComparisonProvider >

#define TGeneratorPlaceType_CLS \
TGeneratorPlaceType<PidType, CounterType, ComparisonProvider >

template< typename PidType, typename CounterType,
		  template <typename> class ComparisonProvider = TDefaultComparisonProvider >
class TGeneratorPlaceType
		: public TGenericPlaceType< std::pair<PidType, CounterType>, ComparisonProvider >
{
	typedef std::pair<PidType, CounterType> 											DataType_t;
	typedef TGeneratorPlaceType<PidType, CounterType, ComparisonProvider> 				ThisType_t;
	typedef TGenericPlaceType< std::pair<PidType, CounterType>, ComparisonProvider > 	BaseType_t;

public:
				TGeneratorPlaceType();
				TGeneratorPlaceType(const ThisType_t& other);

	void 		update_pid_counter(const PidType& pid, CounterType counter);
	void 		remove_pid(const PidType& pid);
};


TGeneratorPlaceType_TARGS
TGeneratorPlaceType_CLS::TGeneratorPlaceType()
{
}

TGeneratorPlaceType_TARGS
TGeneratorPlaceType_CLS::TGeneratorPlaceType(const TGeneratorPlaceType_CLS& other)
		: TGenericPlaceType< DataType_t >(other)
{
}

TGeneratorPlaceType_TARGS
void TGeneratorPlaceType_CLS::update_pid_counter(const PidType& pid, CounterType counter)
{
	for (int i = 0; i < this->mSize; ++i) {
		DataType_t& current = this->mData[i];
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
	add( std::pair<PidType, CounterType>(pid, counter) );
}

TGeneratorPlaceType_TARGS
void TGeneratorPlaceType_CLS::remove_pid(const PidType& pid)
{
	for (int i = 0; i < this->mSize; ++i) {
		DataType_t& current = this->mData[i];
		int cmp = ComparisonProvider<PidType>::compare(current.get_first(), pid);
		if (cmp == 0) {
			BaseType_t::remove_by_index(i);
			return;
		} else if (cmp > 0) {
			return;
		}
	}
}


///

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
struct TFormatter< std::pair< TLeft, TRight > >
{
	inline static size_t format(char* buffer, std::pair< TLeft, TRight>& pair) {
		char *initial_buffer = buffer;
		buffer += sprintf(buffer, "<");
		buffer += TFormatter< TLeft >::format(buffer, pair.get_first());
		buffer += sprintf(buffer, ", ");
		buffer += TFormatter< TRight >::format(buffer, pair.get_second());
		buffer += sprintf(buffer, ">");
		return buffer - initial_buffer;
	}
};


///

typedef std::vector<void*> 		neco_list_t;

typedef void (*deletion_callback_t)(void *);
void neco_list_delete_elts(neco_list_t* list, deletion_callback_t del);

#endif /* _CTYPES_H_ */
