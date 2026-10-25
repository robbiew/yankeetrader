# Trading, port pricing, ownership, and Earth

Recovered from original YT.EXE (main module 1000:67cc–6ae9, 7ccf–8440, 2342–2709 and Earth equipment 6cb3–7cba), with isolated DOSBox evidence under `../yt-combat/experiments/trade-*`. Fixtures are deliberately constructed saved games; transactions execute the original DOS binary.

## Price and supply calculations

For each commodity, let B be its reference price, C its signed port coefficient, S its current supply/remaining demand, and P its daily production:

```
elapsed = current_day - last_day + (current_minutes - last_minutes)/1440
if elapsed < 0 or elapsed > 10: elapsed = 10
S += P * elapsed
P = max(P, S/10)
price = max(1, floor(B * (1 - C*S/(P*1000)) + 0.5))
bill = floor(quantity * price + 0.5)
```

Positive C means the port sells to the player; negative C means it buys. In both directions the transaction reduces S by the quantity. For a buying port, S therefore represents remaining demand, not physical cargo inventory. Prices are computed on docking. Surplus can raise production; treating this as a simple stock cap would be wrong. The negative-time clamp gives ten days of production and needs fixing.

Main 003a–00ac constructs reference prices as `20-5*RND+5*RND`, `30-7*RND+7*RND`, and `40-10*RND+10*RND`. This occurs before the later RANDOMIZE call. Exact initial RNG behavior is not yet established; do not model these as independently reseeded per-login prices without further evidence.

DOS tests bought 10 ore for 100 credits at stock 1000 and for 190 at stock 100. Selling 10 ore to a buying port paid 300 credits. Cargo, cash, and demand/supply changes agree. Small additional fractional stock comes from elapsed production before docking.

## Ownership

An unowned ordinary port's purchase price is `floor((Pore+Porg+Pequipment)/10)+1`; production 100/100/100 produced an actual 31-credit purchase. Earth costs exactly 1,000,000 credits. Purchasing Earth works in DOS despite the manual's prohibition. A successful purchase assigns ownership and increments the player's port counter.

Code also transfers an existing owner's treasury plus sale price to that owner and decrements their port counter on a buyout; this transfer branch has not yet received its own DOS test.

When a player buys goods or Earth equipment, the port treasury receives:

- No owner: zero.
- Purchaser owns port: floor(1% of purchase cost).
- Another player owns port: the entire purchase cost.

The three ownership cases were exercised with a 100-credit ore purchase: treasury increases were 0, 1, and 100. Port purchases deduct cash. Selling cargo does not deposit an equivalent owner commission.

## Earth money exploit

The original DOS game permits Earth ownership and routes another player's equipment spending into Earth's withdrawable treasury. Evidence chain: `trade-earth-buy`, `trade-earth-gear`, `trade-earth-withdraw`, `trade-earth-gear2`, `trade-earth-withdraw2`. The owner pays the one-million-credit initial acquisition cost. A second player then buys 1,000 fighters for 100,000 credits; the owner collects that full 100,000 with `$`. Repeating recycles the expenditure while creating additional fighters. This is a cooperative resource-generation exploit, not a refund to an ordinary lone purchaser. The acquisition cost remains a real initial sink.

The companion validator checks the recorded cash, cargo, treasuries, ownership, and repeated fighter-purchase cycle. Sessions may stop at the command prompt when the scripted emulator deadline expires; persisted transaction state and the recorded transaction messages are the evidence, not an assumption of normal logout.
