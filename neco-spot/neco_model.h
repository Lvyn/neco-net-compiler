#ifndef _MODEL_H_
#define _MODEL_H_

#include "Python.h"
#include "ctypes.h"
#include "checker_api.h"
#include "net_api.h"
#include "ctypes.h"
#include <map>
#include <string>
#include <iostream>

namespace neco
{
    //! Class wrapping the compiled Petri net module.
    //!
    //! This class is a singleton providing every operation available in net_api.h.
    class Model
    {
    public:

	//! Get the unique instance.
	static inline Model& instance() {
	    static Model s_instance;
	    return s_instance;
	}

	//! Destructor.
	~Model();

	//! Get the marking structure in initial state.
	const struct Marking* init() const;

	//! Get a list of successor markings of the marking \a m.
	struct neco_list* succs(const struct Marking* m) const;

	//! Get the hash value of a marking \a m.
	int marking_hash(const struct Marking* m) const;

	//! Compare two markings \a m1 and \a m2.
	int marking_compare(const struct Marking* m1, const struct Marking* m2) const;

	//! Copy a marking \a m.
	const struct Marking* marking_copy(const struct Marking* m) const;

	//! Return a C string representation of a marking \a m.
	char* marking_dump(const struct Marking* m) const;

	//! Get the value of an atomic proposition \a atom in a marking \a m.
	//!
	//! The \a atom argument is the neco identifier of the corresponding
	//! atomic proposition. These identifiers are inferred from formulas.
	int check(const struct Marking* m, int atom) const;

    private:
	//! Private constructor, used by instance method.
	Model();
	//! Copy constructor, disabled: non copyable.
	Model(const Model& other);
	//! Assignment operator, disabled: non copyable.
	const Model& operator=(const Model& other);

    };

}

#endif /* _MODEL_H_ */
