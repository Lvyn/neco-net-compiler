#include <Python.h>
#include <ctime>
#include <fstream>

#include "ctypes.h"
#include "neco_tgba.h"
#include "neco_state.h"
#include "neco_succiter.h"
#include "neco_model.h"

#include <spot/tgbaalgos/dotty.hh>
#include <spot/ltlenv/defaultenv.hh>
#include <spot/ltlast/allnodes.hh>
#include <spot/ltlparse/public.hh>
#include <spot/ltlvisit/simplify.hh>
#include <spot/tgbaalgos/ltl2tgba_fm.hh>
#include <spot/tgbaalgos/sccfilter.hh>
#include <spot/tgbaalgos/emptiness.hh>
#include <spot/tgbaalgos/minimize.hh>
#include <spot/tgbaalgos/rundotdec.hh>
#include <spot/tgbaalgos/reducerun.hh>
#include <spot/tgbaalgos/stats.hh>
#include <spot/tgba/tgbatba.hh>
#include <spot/tgba/tgbaproduct.hh>
#include <spot/misc/timer.hh>
#include <spot/misc/memusage.hh>
#include <cstring>

#include <boost/program_options.hpp>
#include <boost/format.hpp>

namespace po = boost::program_options;


void readline(std::string* dst, std::ifstream& stream) {
    char buf[1024];
    do {
        stream.clear();
        stream.getline(buf, 1024);
        *dst += buf;
    } while( stream.fail() && !stream.eof() );
}

int
main(int argc, char **argv)
{
  spot::timer_map tm;

  bool use_timer = false;

  enum { DotFormula, DotModel, DotProduct, DotCounterExample,
	 EmptinessCheck, StateSpaceSize }
  output = EmptinessCheck;
  bool accepting_run = false;
  bool expect_counter_example = false;
  bool wdba = false;
  char draw = 0;
  std::string formula = "";
  std::string dead = "true";
  std::string echeck_algo = "Cou99";

  po::positional_options_description pos_options;
  pos_options.add("formula", -1);

  po::options_description hidden;
  hidden.add_options()
      // ("formula", po::value<std::string>(&formula), "LTL formula to check")
      ("formula", po::value<std::string>(&formula), "one line file conaining a LTL formula to check")
  ;

  po::options_description visible((boost::format("%s [OPTION]... FORMULAFILE\nOptions") % argv[0]).str());
  visible.add_options()
      ("help,h", "produce help message")
      ("counterexample,C", "compute an accepting run (Counterexample) if it exists")
      ("dead,d", po::value<std::string>(&dead), "use DEAD as property for marking dead states")
      ("echeck,e", po::value<std::string>(&echeck_algo)->default_value("Cou99"),
       "run emptiness check, expect an accepting run")
      ("echeck-na,E", po::value<std::string>(&echeck_algo)->default_value("Cou99"),
       "run emptiness check, expect no accepting run")
      ("draw,g", po::value<char>(&draw), "drawing in dot format depending on arg:\n"
                                         " C: draw an accepting run (counterexample)\n"
                                         " f: draw the automaton of the formula\n"
                                         " m: draw the model state-space\n"
                                         " p: draw the product state-space")
      ("ss-size,k", "compute size of state-space")
      ("times,T", "time the different phases of the execution")
      ("minimize-wdba,W", "enable WDBA minimization")
  ;

  po::options_description cmdline_options;
  cmdline_options.add(hidden).add(visible);

  po::variables_map vm;
  po::store(po::command_line_parser(argc, argv).options(cmdline_options).positional(pos_options).run(), vm);
  po::notify(vm);

  if (vm.count("help") || formula == "") {
      std::cout << visible << std::endl;
      return 1;
  }

  {
      std::ifstream ifile(formula.c_str(), std::ifstream::in);
      if (!ifile.good()) {
          std::cerr << "unable to open formula file" << std::endl;
          exit(1);
      }

      formula = "";
      bool formula_found = false;
      while (!formula_found && !ifile.eof()) {
          readline(&formula, ifile);

          if (formula == "# -d DEAD") {
              dead = "DEAD";
              formula = "";
              continue;
          } else if (formula[0] == '#' || formula == "") {
              formula = "";
              continue;
          } else {
              formula_found = true;
          }
      }
      ifile.close();
  }

  if (formula == "") {
      std::cout << visible << std::endl;
      return 1;
  }

  std::cout << "Formula: " << formula << std::endl;

  if (vm.count("counterexample")) {
      accepting_run = true;
  }

  if (vm.count("echeck")) {
      expect_counter_example = true;
      output = EmptinessCheck;
  }

  if (vm.count("echeck-na")) {
      expect_counter_example = false;
      output = EmptinessCheck;
  }

  if (vm.count("draw")) {
      switch(draw) {
      case 'C':
	  output = DotCounterExample;
	  accepting_run = true;
	  break;
      case 'f':
	  output = DotFormula;
	  break;
      case 'm':
	  output = DotModel;
	  break;
      case 'p':
	  output = DotProduct;
	  break;
      default:
	  std::cerr << "bad argument in --draw/-g option." << std::endl;
	  return -1;
      }
  }

  if (vm.count("ss-size")) {
      output = StateSpaceSize;
  }
  if (vm.count("times")) {
      use_timer = true;
  }
  if (vm.count("minimize-wdba")) {
      wdba = true;
  }

  spot::ltl::default_environment& env =
    spot::ltl::default_environment::instance();

  spot::ltl::atomic_prop_set ap;
  spot::bdd_dict* dict = new spot::bdd_dict();
  const spot::tgba* prop = 0;
  spot::tgba* product = 0;
  const spot::tgba* not_degeneralized = 0;
  spot::emptiness_check_instantiator* echeck_inst = 0;
  int exit_code = 0;
  const spot::ltl::formula* f = 0;
  const spot::ltl::formula* deadf = 0;


  Py_Initialize();
  neco::Model::instance(); // force model instantiation
  neco::tgba* model = 0;


  if (dead == "true") {
      deadf = spot::ltl::constant::true_instance();
  } else if (dead == "false") {
      deadf = spot::ltl::constant::false_instance();
  } else {
      deadf = env.require(dead);
  }

  if (output == EmptinessCheck || output == DotCounterExample) {
      const char* err;
      echeck_inst =
	  spot::emptiness_check_instantiator::construct(echeck_algo.c_str(), &err);
      if (!echeck_inst) {
	  std::cerr << "Failed to parse argument of -e/-E near `"
		    << err <<  "'" << std::endl;
	  exit_code = 1;
	  goto safe_exit;
      }
  }

  tm.start("parsing formula");
  {
      spot::ltl::parse_error_list pel;

      std::cout << "negating the formula" << std::endl;
      std::stringstream ss;
      ss << "!(" << formula.c_str() << ")";
      f = spot::ltl::parse(ss.str(), pel, env, false);
      exit_code = spot::ltl::format_parse_errors(std::cerr, formula.c_str(), pel);
  }
  tm.stop("parsing formula");

  tm.start("reducing formula");
  {
      spot::ltl::ltl_simplifier simplifier;
      const spot::ltl::formula* r = simplifier.simplify(f);
      f->destroy();
      f = r;
  }
  tm.stop("reducing formula");

  if (exit_code)
      goto safe_exit;

  atomic_prop_collect(f, &ap);

  if (output != DotFormula) {
      model = new neco::tgba(&ap, dict, deadf);
  }

  if (output == DotModel) {
      tm.start("dotty output");
      spot::dotty_reachable(std::cout, model);
      tm.stop("dotty output");
      goto safe_exit;
  }

  tm.start("translating formula");

  prop = spot::ltl_to_tgba_fm(f, dict, true /* optimize determinism */);
  tm.stop("translating formula");

  tm.start("reducing A_f w/ SCC");
  {
      const spot::tgba* aut_scc = spot::scc_filter(prop, true);
      delete prop;
      prop = aut_scc;
  }
  tm.stop("reducing A_f w/ SCC");

  if (wdba) {
      tm.start("WDBA minimization");
      const spot::tgba* minimized = 0;
      minimized = minimize_obligation(prop, f);

      if (minimized != prop) {
	  delete prop;
	  prop = minimized;
      }

      tm.stop("WDBA minimization");
  }

  if (output == DotFormula) {
      tm.start("dotty output");
      spot::dotty_reachable(std::cout, prop);
      tm.stop("dotty output");
      goto safe_exit;
  }

  if (output == StateSpaceSize) {
      tm.start("stats_reachable");
      spot::tgba_statistics st = spot::stats_reachable(model);
      tm.stop("stats_reachable");

      std::cout << "the state graph is composed of " << st.states;
      std::cout << " states and " << st.transitions << " edges" << std::endl;

      goto safe_exit;
  }

  if (echeck_inst &&
      ((echeck_inst->max_acceptance_conditions() == 0) ||
       (echeck_inst->max_acceptance_conditions() == 1)))
  {
      not_degeneralized = prop;
      prop = new spot::tgba_sba_proxy(prop);
  }

  product = new spot::tgba_product(model, prop);

  if (output == DotProduct) {
      tm.start("dotty output");
      spot::dotty_reachable(std::cout, product);
      tm.stop("dotty output");
      goto safe_exit;
  }

  assert(echeck_inst);

  {
      spot::emptiness_check* ec = echeck_inst->instantiate(product);
      bool search_many = echeck_inst->options().get("repeated");

      assert(ec);
      do {
          int memused = spot::memusage();
          tm.start("running emptiness check");
          spot::emptiness_check_result* res;

          try {
              res = ec->check();
          }
          catch (std::bad_alloc) {
              std::cerr << "Out of memory during emptiness check."
                        << std::endl;
              exit_code = 2;
              exit(exit_code);
          }
          tm.stop("running emptiness check");


          memused = spot::memusage() - memused;

          if (output != DotCounterExample) {
              ec->print_stats(std::cout);
              std::cout << memused << " pages allocated for emptiness check"
                        << std::endl;
          }


          if (expect_counter_example == !res &&
              (!expect_counter_example || ec->safe()))
              exit_code = 1;

          if (!res) {
              std::cout << "no counterexample found";
              if (!ec->safe() && expect_counter_example) {
                  std::cout << " even if expected" << std::endl;
                  std::cout << "this may be due to the use of the bit"
                            << " state hashing technique" << std::endl;
                  std::cout << "you can try to increase the heap size "
                            << "or use an explicit storage"
                            << std::endl;
              }
              std::cout << std::endl;
              break;
          }
          else if (accepting_run) {
              spot::tgba_run* run;
              tm.start("computing accepting run");
              try {
                  run = res->accepting_run();
              } catch (std::bad_alloc) {
                  std::cerr << "Out of memory while looking for counterexample."
                            << std::endl;
                  exit_code = 2;
                  exit(exit_code);
	      }
              tm.stop("computing accepting run");

              if (!run) {
                  std::cout << "a counterexample exists" << std::endl;
              } else {
                  tm.start("reducing accepting run");
                  spot::tgba_run* redrun =
                      spot::reduce_run(res->automaton(), run);
                  tm.stop("reducing accepting run");
                  delete run;
                  run = redrun;

                  tm.start("printing accepting run");
                  if (output == DotCounterExample) {
                      spot::tgba_run_dotty_decorator deco(run);
                      spot::dotty_reachable(std::cout, res->automaton(),
                                            false, &deco);
                  } else
                      spot::print_tgba_run(std::cout, product, run);
                  tm.stop("printing accepting run");
	      }
              delete run;
          }
          else {
              std::cout << "a counterexample exists "
                        << "(use -C to print it)" << std::endl;
          }
          delete res;
      }
      while (search_many);
      delete ec;
  }

 safe_exit:
  delete echeck_inst;
  delete product;
  delete prop;
  delete not_degeneralized;
  delete model;
  if (f)
      f->destroy();
  delete dict;

  deadf->destroy();

  if (use_timer)
      tm.print(std::cout);
  tm.reset_all();		// This helps valgrind.

  Py_Finalize();

  spot::ltl::atomic_prop::dump_instances(std::cerr);
  spot::ltl::unop::dump_instances(std::cerr);
  spot::ltl::binop::dump_instances(std::cerr);
  spot::ltl::multop::dump_instances(std::cerr);
  spot::ltl::automatop::dump_instances(std::cerr);
  assert(spot::ltl::atomic_prop::instance_count() == 0);
  assert(spot::ltl::unop::instance_count() == 0);
  assert(spot::ltl::binop::instance_count() == 0);
  assert(spot::ltl::multop::instance_count() == 0);
  assert(spot::ltl::automatop::instance_count() == 0);

  exit(exit_code);
}


