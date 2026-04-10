# Digital Energy Grid 
The **Digital Energy Grid (DEG)** represents a paradigm shift toward a unified, interoperable, and intelligent digital infrastructure for the global energy ecosystem. It envisions a world where the flow of **energy**, **information**, and **transactions** are seamlessly synchronized across distributed systems—transforming today’s fragmented landscape into a dynamic, transparent, and equitable grid of the future.

This initiative emerges at the intersection of **energy transition and digital transformation**, where decentralization, electrification, and data-driven intelligence converge. Conceived by the **Foundation for Interoperability in Digital Economy (FIDE)** in collaboration with the **International Energy Agency (IEA)**, DEG aims to establish a common digital backbone for the energy sector—one that enables cross-domain interoperability, fosters innovation, and scales inclusively across geographies.

# Current Version
Version 0.4.0

## Working Group Members

| Name                    | Role                           | Github Username  |
|-------------------------|--------------------------------|------------------|
| Ravi Prakash            | Maintainer, Protocol Architect | @ravi-prakash-v  |
| Pramod Varma            | Maintainer, Reviewer           | @pramodkvarma    |
| Sujith Nair             | Reviewer                       | @sjthnrk         |
| Ameet Deshpande         | Subject Matter Expert          | @ameetdesh       |
| Vish Ganti              | Subject Matter Expert          | @vganti1         |
| Anusree Jayakrishnan    | Reviewer                       | @Anusree-J       |
| Anirban Sinha           | Implementation Specialist      | @i-am-anirban-95 |
| Tanmoy Adhikary         | Implementation Specialist      | @TANMOYDADA      |

## Introduction
A DEG is a decentralized / federated digital ecosystem that enables transactions that result in the transfer of energy from a energy producer to an energy provider. The energy producer isn't necessarily the energy generator, rather an entity that represents the energy supply. Similarly, an energy consumer isn't necessarily an appliance or a household, but more like a consumer that represents the energy demand. For example, an energy producer can be an EV charging station while a consumer can be an EV. Likewise, an energy producer can be a Solar Plant owner that supplies energy to the Grid, or a Distribution Company that supplies energy to homes. Similarly, an energy consumer can be a vehicle that needs charging; a home appliance that needs electricity to run; or even the distribution company than needs energy from the power generation companies (like power plants). 

An important thing to note here is that when it comes to electrical energy, the energy transfer is not always from power plants to the appliances. In many cases, simple households with an energy surplus can also feed it back to the electricity grid and avail commercial benefits like reduced electricity bills. DEG enables creation of such contracts as well. 

Just like physical goods can be consumed or stored, energy can _also_ be _consumed_ or _stored_. DEGs allow creation of energy contracts that not only enable the consumption of energy, but also the storage of energy (in batteries, capacitors, etc). 

> **Note :** DEG does NOT transfer "Energy" in its physical form. Enery transfer is still done via physical infrastructures like Generators, transmission lines, transformers, inverters, adaptors etc. UEI only facilites the creation of the energy transfer contract (order) that ultimately results in the physical transfer (fulfillment).

## Implementing the specification

To understanding how to implement use cases on DEGs, click [here](./docs/implementation-guides/v2)

### Platform profile (BAP / BPP / catalog / discovery / ledger + beckn-onix)

For a **normative extension** that ties together **Beckn ONIX**, **catalog**, **discovery**, **ledger**, and the **DEG schema bundle** for full-stack platforms (utility + aggregator), see:

- **[specification/deg-platform-profile/README.md](./specification/deg-platform-profile/README.md)** — index  
- **[specification/deg-platform-profile/DEG-Platform-Profile-Specification.md](./specification/deg-platform-profile/DEG-Platform-Profile-Specification.md)** — specification  
- **[specification/deg-platform-profile/schema/](./specification/deg-platform-profile/schema/)** — schema bundle manifest (draft; **Beckn v2** refs)  
- **[specification/schema/BECKN_V2_ALIGNMENT.md](./specification/schema/BECKN_V2_ALIGNMENT.md)** — DEG schemas vs **protocol-specifications-v2**  
- **[testnet/deg-platform-devkit/](./testnet/deg-platform-devkit/)** — **developer kit + examples** (Postman, ONIX via demand-flex compose, JSON samples)  
- **[specification/deg-platform-profile/developer-kit/](./specification/deg-platform-profile/developer-kit/)** — pointer to `testnet/deg-platform-devkit/`

## Acknowledgements

The author(s) of this specification would like to thank the following volunteers for their contribution to the development of this specification
