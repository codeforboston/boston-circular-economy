# Contributing Guide

## Circular Economy Team Norms

As a volunteer-driven team at Code for Boston, we are designing and developing a circular-economy website that helps Boston residents repair and reuse more items rather than throw them out. To learn more about Code for Boston and how to join it, check out their [website](https://codeforboston.org/).

### Onboarding

We need to minimize friction to first contribution. To that end, we want to have a new member speak in a meeting with us as soon as possible.

When a newcomer enters the room, we will progress as follows:

- Pause the current topic of discussion, making note of where we are
- Ask two questions:
   - How might you like to contribute to a volunteer project like this one?
   - What is an item that you'd like to see reused, repaired, or repurposed instead of being thrown out?
 - Direct the newcomer to onboarding resources and whichever room is most relevant to their expressed interests
 - Continue the meeting where we left off

Onboarding resources are in the [onboarding folder](https://drive.google.com/drive/folders/1VwGplVI0PalVvoBEQXzUnyOGlLbnntGg), with the [onboarding document](https://docs.google.com/document/d/1ja4MXAvy5s0U7pD5Xx5rr62x4_BU_biYdjbRFC0GQyU/edit?tab=t.0#heading=h.80ojjizca2at) as the main entry point.

### Contributing

There is a lot of room for flexibility in contributing! We want volunteers to feel comfortable taking initiative and getting involved on day one. The following sections offer some structure and guidelines for contributing, but are not exhaustive.

#### Creating structured work

This is the primary work mode for tech leads. It is usually the case that we have more engineering resources than we have ticketed work. Creating tickets allows us to tap into those resources. Tickets should have a clear scope, and all necessary context either present in the ticket itself, or links to documents with context.

General guidance for creating structured work:

- Keep the work scope small and atomic. Reviewing code is much easier in smaller PRs.
- Be conscious of dependencies. Parallelizable work is ideal.

#### Proposing work

We welcome new ideas and effort that isn't already predefined. The best way to venture off in a new direction is to first talk about it with the team. We share relevant past context, and make sure the work would not negatively impact existing or upcoming work. Then the person proposing the work can go off and build, presenting a prototype, or exploration, or completed feature, depending on what seems most appropriate.

You can propose work either by posting in [Slack](https://inviter.co/cfb-slack) or by talking about it during a hack night. If you want to talk about it during a hack night, place an item in the [agenda](https://docs.google.com/document/d/1qUKacbc9PmjSk93_FBUlVJBr6ZguFLpsNJ173IN11Ag/edit?tab=t.0#heading=h.ngglse4110bn).

#### Working on predefined work

Predefined work will exist as tickets with a defined scope of work. You can assign tickets to yourself through our [project management tool](https://github.com/orgs/codeforboston/projects/21). You can also ask for clarifying information, make suggestions, or propose alternatives as you see fit. You can do this either in Slack, the ticket itself, or during a hack night.

You may, in the process of working on predefined work, discover it is more complex than originally understood. You are encouraged to break up the work into smaller parts. We prefer a stream of frequent, small PRs to waiting months for a giant PR.

You may also find issues in the codebase adjacent to the work area. You can include small changes in those areas, but for anything significant, you are encouraged to open a separate PR.

If you find that you are unable to continue a ticket, please post in Slack, and take your head off of the ticket. If we haven't heard from you in 2 weeks, we will assume you left the project and we will reassign the work.

#### Reviewing code

The only way to get code merged is to get code reviewed. This is a fairly safe and non-committal way to contribute to this project. By reviewing code, not only do you increase confidence in our codebase, but you also develop a better understanding of the codebase yourself!

Aim to review at least two PRs for every one that you submit. We want redundant reviews. Partial reviews are also completely fine; just explain which parts you reviewed, and which you did not.

See this [document](https://docs.google.com/document/d/104KahwT6rH01jPD-wx9aKHZOkd-ZYY_11-3SG5z9Z80/edit?tab=t.0) for specific guidelines for reviewing code.

#### Using AI

AI use is encouraged! Whether it is writing code, or writing documents, AI can accelerate our progress. There are two caveats with using AI:
1. You should understand, and review everything you submit. AI hallucinates, and hallucinations aggregate.
2. Keep in mind that the real bottleneck is reading and reviewing AI generated content. Be conscious of the scope of what you generate. Someone has to read all of it, so keep them in mind.

#### Communication

Some guidelines on communicating on Slack:

- Provide context in your communications with links to docs, tickets, code, resources, etc.
- Err on the side of over-communicating. Avoid flooding the chat with what you share. Keep posts less than a page height. If you have more than that to post, instead post a summary and link to more resources in the [Google Drive](https://drive.google.com/drive/folders/0AOq9AjRQulY0Uk9PVA).
- Use Slack threads to continue conversations. This keeps conversations organized and focused.
- Slack should not be used directly as documentation.

Some guidelines in communicating during hack nights:

- Pay attention to who is talking, and how much. If you notice someone who hasn't spoken much wants to say something, give them the floor.
- Give newcomers, or more junior contributors, earlier opportunities to speak.
- It is okay to have periods of silence. This gives more people opportunities to speak.

#### Leadership communication

If you are leading some part of the project, regularly communicate updates and decisions made. How you do that is up to you, as long as it is consistent and visible. We suggest posting in Slack channels or keeping a log document. 

Please also communicate conversations you had with other organizations relevant to our project.

#### Documentation

Document software decisions in implementation details, code-discussion summaries, GitHub PRs, or tickets. Document product resources and research in the [Google Drive](https://drive.google.com/drive/folders/0AOq9AjRQulY0Uk9PVA).

## Prototyping

### Client-Side Prototyping

Use `/dev/` for prototyping and experimentation in the client app. Pages under `client/src/pages/dev/` are accessible at `/dev/` in development and listed on the dev index. Prototypes don't need to meet production standards; use them to explore ideas before building the real thing. When a prototype is ready to graduate, move it out of `client/src/pages/dev/` into the appropriate location.
