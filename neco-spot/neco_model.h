#ifndef _NECO_MODEL_H_
#define _NECO_MODEL_H_

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
//! A singleton class providing every operation available in net_api.h.
class Model
{
public:

                            	//! Get the unique instance.
	inline static Model&        instance();

	const struct Marking*       marking_copy(const struct Marking* m) const;
                                ~Model();

	const struct Marking*       initial_marking() const;
	neco_list_t*                succs(const struct Marking* m) const;

	int                         marking_hash(const struct Marking* m) const;
	int                         marking_compare(const struct Marking* m1, const struct Marking* m2) const;

                                //! Return a C string representation of a marking \a m.
	char*                       marking_dump(const struct Marking* m) const;

                            	//! Get the value of an atomic proposition \a atom in a marking \a m.
                            	//!
                            	//! The \a atom argument is the neco identifier of the corresponding
                            	//! atomic proposition. These identifiers are inferred from formulas.
	int                         check(const struct Marking* m, int atom) const;

private:
                                //! Private constructor, used by instance method.
                                Model();
                                //! Copy constructor, disabled: non copyable.
                                Model(const Model& other);
                            	//! Assignment operator, disabled: non copyable.
                            	const Model& operator=(const Model& other);
};

Model& Model::instance()
{
    static Model s_instance;
    return s_instance;
}

}

#endif /* _NECO_MODEL_H_ */
