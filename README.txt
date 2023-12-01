==     ====== ====== ======
==     ====== ==  == ==
==     ==  == ====== =====
==     ==  == ==  == =====
====== ====== ==   = ==
====== ====== ==   = ======

This is Lore, an AI worldbuilding/wiki-editing assistant specially tailored to the Constructed Worlds Wiki.

As of 1 December 2023, Lore has several features accessible through the Constructed Worlds Wiki Discord server.

COMMAND LIST
$lore.chat (prompt)
	This is the first command that was added to Lore. It allows users to give prompts to two GPT models and stores message history on a per-user basis. Patrons have access to the more expensive GPT-4-Turbo, one of OpenAI's most powerful models.
	In essence, the prompt passed through the command is appended with contextual information relevant to the wiki such as its administration and purpose. GPT-3.5-Turbo, available to non-Patrons, does not seem as capable in its processing of this context.

$lore.help
	Simply lists all available commands to users.

$lore.read (Constructed Worlds Wiki page title exactly as appears on the site)
	This command makes GPT load the text content of a page and create a 1999 character summary, which is then stored in the memory dictionary. If used before a '$lore.chat' command, Lore will be able to use the summary to answer questions or provide anaylsis.
	At the moment, the text of pages being summarized seems only to be from the introductory sections of articles. Anything under headers seems to be missed. Eventually, read will be limited to page sections, allowing more detail-oriented summarization.

$lore.wipe
	This command clears the memory dictionary for the user. Especially with GPT-3.5, more frequent use of this command allows for more coherent responses from the '$lore.chat' feature. GPT-4 does not need this command as frequently.

$lore.purge
	This command is exclusively for use by Conworlds admins. It clears the memory dictionary for all users and resets the use-counter for non-Patrons.
