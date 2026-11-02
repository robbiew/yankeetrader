package game

import (
	"errors"
	"math/rand"
	"strings"
)

// The original initializer's DATA syllables (duplicates preserve their weights).
// YT-INIT.EXE SHA256: 601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2.
// DATA rows: file 0x33b0..0x4716, excluding the quoted *** sentinel.
// SHA256 of these comma-joined 908 entries:
// 8a59a909d232084d89a82db77339f680475c3187aef96ef0ce6444bd0b4002b7.
const dosPortSyllableData = `ing,bat,ton,son,tha,cut,ed,stro,a,e,i,o,u,y,ook,eek,unt,or,ar,er,ma,ba,ra,oi,wer,war,cut,rut,mud,cad,cud,cod,er,wo,ang,ong,thro,thru,thra,ou,ca,ba,ra,ta,org,orp,ick,ock,ack,dow,dog,ann,al,ind,moo,boo,zoo,too,who,town,ville,burg,uck,aan,ton,tan,tor,og,den,dan,don,in,on,an,ly,jo,do,flat,ban,ash,ent,bol,ish,bom,tion,ound,ace,ode,bra,ive,rid,upt,ant,ted,flam,dul,ism,ture,ock,uzzy,asm,liv,gog,sau,au,ness,oot,scro,the,erm,ium,tri,out,oint,nom,mer,erk,our,fem,ale,dis,dix,cem,cha,zy,vis,oast,oad,pred,pes,non,met,tin,hop,gy,gam,xan,ex,croo,clea,bro,crim,nud,mas,hy,her,him,ex,won,for,maar,tun,nut,mad,dam,god,rod,wag,hut,mat,sum,mus,tor,rot,bug,dell,bag,fag,gag,rag,sum,rat,tar,umb,mix,max,der,red,mur,rum,hot,cut,ute,man,bot,star,port,net,pla,ship,ore,equ,org,oat,ote,oll,all,ill,ear,bro,rom,bre,bri,xig,sox,six,sex,sax,sux,pi,qui,quo,qua,que,pop,bop,flo,fla,fle,ele,tron,ic,mon,tor,spea,ker,raid,ship,box,ette,lan,der,cal,car,pet,org,flop,flap,flip,ink,wow,mis,sile,plas,ma,bolt,gun,bang,shield,cloak,anti,glen,ade,fern,wood,tree,pond,lake,river,sky,red,blue,white,green,pink,bi,orange,yellow,slow,fast,half,big,small,tiny,purple,main,sub,trac,mini,wiz,ard,demon,rock,metal,hull,full,stic,stat,ic,fere,inter,space,dock,ice,one,two,three,four,five,six,seven,eight,nine,ten,eleven,twelve,new,thirteen,teen,boat,end,good,cove,hole,reef,bad,light,dark,little,old,mono,stereo,quad,triple,single,worm,snake,le,sion,ion,cannon,if,she,he,double,reactor,turbo,lift,proton,torpedo,warp,drive,hope,fear,happy,cat,unit,computer,central,serial,parallel,door,hatch,shoot,fire,pan,tube,display,key,board,mouse,trak,ball,trade,sell,buy,lost,last,word,work,up,down,out,throu,under,over,left,right,dead,live,forsaken,place,lonely,yes,silver,gold,credit,rich,poor,king,prince,princess,darth,vader,walker,toad,frog,turtle,lion,moose,breath,body,soul,cry,love,smile,klick,black,suck,sock,sick,sack,coal,nuclear,oil,water,oxygen,less,void,empty,vacume,moon,asteroid,planet,ring,nova,super,event,horizon,broken,fix,repair,no,dino,saur,rex,park,jeep,truck,robot,droid,castle,wolf,lamb,chop,burger,roll,bun,pickle,radiation,danger,safe,bar,drink,farm,factory,food,eat,kill,kiss,kick,push,pull,button,lever,awful,wonderful,many,few,men,women,boy,girl,kid,son,wife,daughter,husband,tire,rim,cap,hub,trunk,hood,wind,rain,snow,thunder,twist,earth,volcano,ocean,sea,world,marine,lick,bite,ping,pong,joy,stick,crew,worth,thing,life,death,shot,run,away,sleep,wake,shore,leave,land,piss,beer,wine,whiskey,card,house,pool,table,pin,screw,pay,mega,kilo,micro,brain,giga,tetra,radio,beam,tune,antenna,dish,luck,alien,xannor,merc,sale,price,quarter,maxi,top,bottom,center,fail,try,smell,virus,trojan,horse,modem,game,room,boss,captain,mutiny,officer,science,vid,mine,boom,able,great,blood,nose,eyes,hand,foot,feet,mouth,teeth,bone,cave,elec,finger,open,close,stuck,hate,sink,pipe,drain,watt,circuit,queen,chip,wire,power,torus,rotate,binary,crap,puke,spit,look,that,this,short,cheap,free,bird,chicken,ranch,clear,wave,ride,bow,stern,aft,fore,more,data,bit,byte,disk,mother,father,brother,sister,wall,floor,window,shut,gram,ounce,pound,ton,mile,inch,yard,meter,centi,milli,fusion,fission,sniff,ugly,pretty,nice,rotten,muddy,sandy,flower,pot,thorn,leaf,sexy,talk,trans,nude,naked,lick,strip,strap,bare,bear,deer,dear,holo,deck,bridge,butt,hip,plant,sword,knife,armor,murder,rape,pilliage,burn,rob,give,take,show,extra,buck,proof,shake,fries,illegal,widow,maker,ass,quick,sand,some,laser,freak,tooth,nail,hook,crook,pirate,hyper,grass,sun,fish,breed,dick,slit,bush,greed,insect,beast,cook,arm,leg,knee,elbow,ceti,alpha,beta,omega,burbon,vodka,scotch,corn,wheat,grain,alcohol,drunk,stoned,joint,bong,smoke,year,day,week,time,century,millenium,hour,minute,second,first,third,engine,impulse,thrust,money,platinum,iron,lead,titanium,uranium,steel,plastic,glass,meteor,comet,card,dice,poker,gamble,slot,machine,cool,cold,hot,warm,frozen,liquid,gas,matter,crimsom,blush,scarlet,dwarf,monster,burning,giant,puppy,puss,kitten,dragon,lizard,snag,snatch,grab,grub,fly,crash,disease,plague,revolt,civil,rest,fuel,energy,motor,servo,control,panel,fever,neutron,electron,storm,acid,base,melt,freeze,thaw,glad,wreck,apple,birth,death,kong,blank,draw,burp,fart,belch,itch,scratch,jump,hop,wiggle,angry,lash,large,huge,egg,couch,potatoe,boron,misty,stupid,smart,genious,baron,lord,mess,baggage,plane,air,hammer,wrench,dream,saw,drill,dill,pad,shirt,shoes,pants,dress,blouse,hat,panties,shorts,sad,jock,rub,code,cube,square,pyramid,rectangle,circle,cover,bull,cow,udder,whip,chain,kinky,pie,cake,aqua,island,doctor,nurse,ruin,heal,heel,toe,slave,destiny,breast,limb,equal,penny,share,shore,sure,tour,stare,fare,ware,hair,skin,monkey,gorilla,camel,kangeroo,alligator,crocodile,tear,swamp,mire,bog,tractor,lightning`

var dosPortSyllables = strings.Split(dosPortSyllableData, ",")

// dosPortName follows the recovered chunk rule and casing from 23e4..2605.
// Its Go PRNG and integer sampling deliberately do not reproduce QB RND or MBF
// rounding at floating-point boundaries. It makes no uniqueness promise.
func dosPortName(rng *rand.Rand) string {
	count := int(3*rng.Float64()*rng.Float64()) + 2
	var name strings.Builder
	for i := 0; i < count; i++ {
		part := dosPortSyllables[rng.Intn(len(dosPortSyllables))]
		if len(part) > 4 {
			name.WriteByte(' ')
			part = strings.ToUpper(part[:1]) + part[1:]
		}
		name.WriteString(part)
	}
	result := strings.TrimPrefix(name.String(), " ")
	return strings.ToUpper(result[:1]) + result[1:]
}

// generateDOSPorts replaces only the ports of a newly constructed world. All
// randomness comes from the caller's seeded Go RNG: this is a rules adaptation,
// not an exact replay of the DOS generator or its random draw sequence.
//
// Ports 1..4 use sectors 1,3,5,7. A finite shuffle supplies the remaining unique
// locations. DOS marked 1,2,3,4 as occupied instead and could overwrite 5/7;
// retaining unique, reachable ports is an intentional correction.
//
// Production is 1000..32766 with signed 1..100 coefficients, one selling and
// two buying goods. Full stocks materialize ten initial production days at the
// current world clock, avoiding a backdated watermark or replayed maintenance.
func generateDOSPorts(w *World, rng *rand.Rand) error {
	if w == nil || rng == nil || w.Created.IsZero() || len(w.Sectors) < 8 || len(w.Sectors) > 3000 {
		return errors.New("DOS-style ports require a new valid world and RNG")
	}
	if len(w.Players) != 0 || len(w.Teams) != 0 {
		return errors.New("port generation requires an empty new world")
	}
	for id := 1; id <= len(w.Sectors); id++ {
		if w.Sectors[id] == nil || w.Sectors[id].ID != id {
			return errors.New("port generation requires contiguous sectors")
		}
	}
	count := min(1000, len(w.Sectors))
	locations := make([]int, 0, count)
	occupied := map[int]bool{}
	for _, id := range []int{1, 3, 5, 7} {
		locations = append(locations, id)
		occupied[id] = true
	}
	choices := make([]int, 0, len(w.Sectors)-4)
	for id := 2; id <= len(w.Sectors); id++ {
		if !occupied[id] {
			choices = append(choices, id)
		}
	}
	for i := 0; i < count-4; i++ {
		j := i + rng.Intn(len(choices)-i)
		choices[i], choices[j] = choices[j], choices[i]
		locations = append(locations, choices[i])
	}
	ports := make(map[int]*Port, count)
	for i, sector := range locations {
		id := i + 1
		port := &Port{ID: id, Sector: sector, Updated: w.Created.UTC()}
		for good := 0; good < 3; good++ {
			port.Production[good] = float64(1000 + rng.Intn(31767))
			port.Supply[good] = 10 * port.Production[good]
		}
		for good := 0; good < 3; good++ {
			port.Coefficient[good] = -float64(1 + rng.Intn(100))
		}
		if id == 1 {
			port.Name = "Earth"
		} else {
			port.Name = dosPortName(rng)
		}
		selling := 2 - rng.Intn(3)
		port.Coefficient[selling] = -port.Coefficient[selling]
		ports[id] = port
	}
	// Publish only after all admission checks and candidate construction succeeded.
	for _, sector := range w.Sectors {
		sector.Port = 0
	}
	for _, port := range ports {
		w.Sectors[port.Sector].Port = port.ID
	}
	w.Ports = ports
	return nil
}
