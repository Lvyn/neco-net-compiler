#ifndef _NECO_STATE_H_
#define _NECO_STATE_H_

#include "neco_model.h"
#include <spot/kripke/kripke.hh>

struct Marking;

namespace neco {

//! A state in neco::tgba.
//!
//! This class wraps a neco Marking structure to represent states inside
//! the transition based generalized buchi automata.
class state final
    : public spot::state
{
public:
					//! Constructor that builds the state from a marking.
					state(const Marking* marking);

	virtual                             ~state();

					//! Comparison operation on states.
					//!
					//! Compares the contained neco Marking.
	virtual int                         compare(const spot::state* other) const override;

                                        //! Get hash value of the state.
	virtual size_t                      hash() const override;

                                        //! Creates a copy of the Marking.
	virtual spot::state*                clone() const override;

    inline const struct Marking*        get_marking() const         { return m_marking; }

private:
					//! Copy constructor, disabled: non copyable
					state(const state& other) = delete;

					//! Assignment operator, disabled: non copyable
	const state&                    operator=(const state& other) = delete;

private:
	const Marking*                      m_marking; //!< neco Marking that the state represents.
};
}

#endif /* _NECO_STATE_H_ */
