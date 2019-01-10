#include <Python.h>
#include <ctime>
#include <fstream>

#include "ctypes.h"
#include "neco_tgba.h"
#include "neco_state.h"
#include "neco_succiter.h"
#include "neco_model.h"

#include <spot/tl/defaultenv.hh>
#include <spot/tl/formula.hh>
#include <spot/tl/parse.hh>
#include <spot/twaalgos/translate.hh>
#include <spot/twaalgos/stats.hh>
#include <spot/twaalgos/emptiness.hh>
#include <spot/twaalgos/dot.hh>
#include <spot/twa/twaproduct.hh>
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
checked_main(int argc, char **argv)
{
  spot::timer_map tm;

  bool use_timer = false;

  enum { DotFormula, DotModel, DotProduct, EmptinessCheck, StateSpaceSize }
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
                                         " f: draw the automaton of the formula\n"
                                         " m: draw the model state-space\n"
                                         " p: draw the product state-space")
      ("ss-size,k", "compute size of state-space")
      ("times,T", "time the different phases of the execution")
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

  spot::default_environment& env =
    spot::default_environment::instance();

  spot::atomic_prop_set ap;
  spot::bdd_dict_ptr dict = spot::make_bdd_dict();
  spot::twa_graph_ptr prop = 0;
  spot::emptiness_check_instantiator_ptr echeck_inst = 0;
  int exit_code = 0;
  spot::formula f = 0;
  spot::formula deadf = 0;
  std::shared_ptr<neco::tgba> model = 0;
  spot::twa_ptr product = 0;

  Py_Initialize();
  neco::Model::instance(); // force model instantiation

  if (dead == "true") {
    deadf = spot::formula::tt();
  } else if (dead == "false") {
    deadf = spot::formula::ff();
  } else {
    deadf = env.require(dead);
  }

  if (output == EmptinessCheck) {
      const char* err;
      echeck_inst =
	  spot::make_emptiness_check_instantiator(echeck_algo.c_str(), &err);
      if (!echeck_inst) {
	  std::cerr << "Failed to parse argument of -e/-E near `"
		    << err <<  "'" << std::endl;
	  exit_code = 1;
	  goto safe_exit;
      }
  }

  tm.start("parsing formula");
  {
      spot::parse_error_list pel;

      std::cout << "negating the formula" << std::endl;
      std::stringstream ss;
      ss << "!(" << formula.c_str() << ")";
      auto pf = spot::parse_infix_psl(ss.str(), env, false);
      exit_code = pf.format_errors(std::cerr);
      f = pf.f;
  }
  tm.stop("parsing formula");

  if (exit_code)
      goto safe_exit;

  tm.start("translating formula");
  {
    spot::translator tr(dict);

    // Are we using an emptiness check that requires a Büchi
    // automaton?
    if (echeck_inst &&
	((echeck_inst->max_sets() == 0) ||
	 (echeck_inst->max_sets() == 1)))
      tr.set_type(spot::postprocessor::BA);

    prop = tr.run(f);
  }
  tm.stop("translating formula");

  atomic_prop_collect(f, &ap);

  if (output == DotFormula) {
      tm.start("dotty output");
      spot::print_dot(std::cout, prop);
      tm.stop("dotty output");
      goto safe_exit;
  }

  model = std::make_shared<neco::tgba>(&ap, dict, deadf);

  if (output == DotModel) {
      tm.start("dotty output");
      spot::print_dot(std::cout, model);
      tm.stop("dotty output");
      goto safe_exit;
  }

  if (output == StateSpaceSize) {
      tm.start("stats_reachable");
      spot::twa_statistics st = spot::stats_reachable(model);
      tm.stop("stats_reachable");

      std::cout << "the state graph is composed of " << st.states;
      std::cout << " states and " << st.edges << " edges" << std::endl;

      goto safe_exit;
  }

  product = spot::otf_product(model, prop);

  if (output == DotProduct) {
      tm.start("dotty output");
      spot::print_dot(std::cout, product);
      tm.stop("dotty output");
      goto safe_exit;
  }

  assert(echeck_inst);

  {
      auto ec = echeck_inst->instantiate(product);
      bool search_many = echeck_inst->options().get("repeated");

      assert(ec);
      do {
          int memused = spot::memusage();
          tm.start("running emptiness check");
          spot::emptiness_check_result_ptr res;

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

	  ec->print_stats(std::cout);
	  std::cout << memused << " pages allocated for emptiness check"
		    << std::endl;

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
              spot::twa_run_ptr run;
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
		  run = run->reduce();
                  tm.stop("reducing accepting run");

                  tm.start("printing accepting run");
		  std::cout << *run;
                  tm.stop("printing accepting run");
	      }
          }
          else {
              std::cout << "a counterexample exists "
                        << "(use -C to print it)" << std::endl;
          }
      }
      while (search_many);
  }

 safe_exit:
  if (use_timer)
      tm.print(std::cout);
  tm.reset_all();		// This helps valgrind.

  Py_Finalize();
  return exit_code;
}

int
main(int argc, char **argv)
{
  int exit_code = checked_main(argc, argv);
  // Make sure we have freed everything.
  assert(spot::fnode::instances_check());
  exit(exit_code);
}
