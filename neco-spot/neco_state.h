#ifndef _NECO_STATE_H_
#define _NECO_STATE_H_

#include "neco_model.h"
#include <spot/tgba/state.hh>

struct Marking;

namespace neco {

    //! A state in neco::tgba.
    //!
    //! This class wraps a neco Marking structure to represent states inside
    //! the transition based generalized buchi automata.
    class state: public spot::state
    {
    public:
	//! Constructor
	//!
	//! Builds the state from a marking structure.
	state(const struct Marking* marking);

	//! Destructor
	virtual ~state();

	//! Comparison operation on states.
	//!
	//! Compares the contained neco Marking structures.
	virtual int compare(const spot::state* other) const;

	//! Get hash value of the state.
	virtual size_t hash() const;

	//! Clone a state.
	//!
	//! Creates a copy of the Marking structure.
	virtual spot::state* clone() const;

	//! Get the contained Marking structure.
	inline const struct Marking* get_marking() const {
	    return m_marking;
	}

    private:
	//! Copy constructor, disabled: non copyable
	state(const state& other);

	//! Assignment operator, disabled: non copyable
	const state& operator=(const state& other);

    private:
	const Marking* m_marking; //!< neco Marking structure that the state represents.
    };
}

#endif /* _NECO_STATE_H_ */
