"""Follow-up active-planet gate controls after source RNG-shift discovery.

The original eight-case writer stays byte-for-byte preserved. This wrapper adds
only two separately declared fixture contexts, then invokes its unchanged runner.
"""
import recover_maintenance_occupied as capture

CASES={
 'wanderer-active-rejection':{'planets':[(2787,2,'Occupied Haven',-1,500000)],'forces':[]},
 'base-active-rejection':{'planets':[(20,2,'Occupied Haven',-1,500000)],'forces':[]},
}
capture.CASES=CASES

if __name__=='__main__':capture.main()
