import cProfile
import net

cProfile.run('net.state_space()', 'profile.stats')
