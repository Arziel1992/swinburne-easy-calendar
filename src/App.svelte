<script>
    // Svelte 5 Runes for State Management
    let viewMode = $state('list');
    let searchQuery = $state('');
    let selectedCohort = $state('Higher Education');
    let selectedType = $state('All');
    let intakesOnly = $state(false);

    const today = new Date();
    let currentMonth = $state(new Date(today.getFullYear(), today.getMonth(), 1));

    // Get available years from data directory
    const dataModules = import.meta.glob('./data/20*.json');
    const availableYears = Object.keys(dataModules)
        .map((path) => Number(path.match(/\/(\d{4})\.json$/)[1]))
        .sort((a, b) => b - a);

    const currentRealYear = today.getFullYear();
    const defaultYear = availableYears.includes(currentRealYear)
        ? currentRealYear
        : availableYears[0] || currentRealYear;

    let academicYear = $state(defaultYear);
    let calendarData = $state([]);

    $effect(() => {
        const path = `./data/${academicYear}.json`;
        if (dataModules[path]) {
            dataModules[path]().then((mod) => {
                calendarData = mod.default || mod;
            });
        } else {
            calendarData = [];
        }
    });

    // Extract unique taxonomies for dropdowns dynamically
    let cohorts = $derived([
        'All',
        ...new Set(calendarData.map((item) => item.cohort)),
    ]);
    let periodTypes = $derived([
        'All',
        ...new Set(calendarData.map((item) => item.type)),
    ]);

    // Visual mappings
    const typeColors = {
        Semester: 'bg-blue-100 text-blue-800 border-blue-300',
        Block: 'bg-purple-100 text-purple-800 border-purple-300',
        Term: 'bg-amber-100 text-amber-800 border-amber-300',
        'Study Period': 'bg-emerald-100 text-emerald-800 border-emerald-300',
        'Teaching Period': 'bg-rose-100 text-rose-800 border-rose-300',
        Quarter: 'bg-cyan-100 text-cyan-800 border-cyan-300',
    };

    // Svelte 5 Derived State for the filtration engine
    let filteredData = $derived(
        calendarData.filter((term) => {
            const matchesSearch = term.period
                .toLowerCase()
                .includes(searchQuery.toLowerCase());
            const matchesCohort =
                selectedCohort === 'All' || term.cohort === selectedCohort;
            const matchesType =
                selectedType === 'All' || term.type === selectedType;
            const matchesIntake = !intakesOnly || term.intake;
            return (
                matchesSearch && matchesCohort && matchesType && matchesIntake
            );
        }),
    );

    // Utility logic
    const formatDate = (dateStr) => {
        if (!dateStr) return null;
        return new Date(dateStr).toLocaleDateString('en-AU', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
        });
    };

    let daysInMonth = $derived(
        new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() + 1,
            0,
        ).getDate(),
    );
    let firstDayOfMonth = $derived(
        new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth(),
            1,
        ).getDay(),
    );
    let startOffset = $derived(firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1);

    const nextMonth = () =>
        (currentMonth = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() + 1,
            1,
        ));
    const prevMonth = () =>
        (currentMonth = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth() - 1,
            1,
        ));

    const isDateOnDay = (dateStr, dayNumber) => {
        if (!dateStr) return false;
        const d = new Date(dateStr);
        return (
            d.getFullYear() === currentMonth.getFullYear() &&
            d.getMonth() === currentMonth.getMonth() &&
            d.getDate() === dayNumber
        );
    };

    const isDayInRange = (startStr, endStr, dayNumber) => {
        if (!startStr || !endStr) return false;
        const current = new Date(
            currentMonth.getFullYear(),
            currentMonth.getMonth(),
            dayNumber,
        );
        const start = new Date(startStr);
        const end = new Date(endStr);
        current.setHours(0, 0, 0, 0);
        start.setHours(0, 0, 0, 0);
        end.setHours(0, 0, 0, 0);
        return current >= start && current <= end;
    };
</script>

<div class="min-h-screen p-4 md:p-8 font-sans text-neutral-900">
    <header class="max-w-7xl mx-auto mb-6">
        <div
            class="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-4"
        >
            <div>
                <div class="flex items-center gap-3 mb-2">
                    <div class="bg-red-600 p-2 rounded-lg text-white">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="28"
                            height="28"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            ><rect
                                width="18"
                                height="18"
                                x="3"
                                y="4"
                                rx="2"
                                ry="2"
                            /><line x1="16" x2="16" y1="2" y2="6" /><line
                                x1="8"
                                x2="8"
                                y1="2"
                                y2="6"
                            /><line x1="3" x2="21" y1="10" y2="10" /></svg
                        >
                    </div>
                    <h1 class="text-3xl font-bold tracking-tight">
                        Swinburne Unified Calendar
                    </h1>
                </div>
                <p class="text-neutral-600 max-w-2xl">
                    Use the period type toggles to isolate overlapping
                    schedules.
                </p>
            </div>

            <div class="flex bg-neutral-200 p-1 rounded-lg">
                <button
                    onclick={() => (viewMode = 'list')}
                    class="flex items-center gap-2 px-4 py-2 rounded-md font-semibold text-sm transition-all {viewMode ===
                    'list'
                        ? 'bg-white shadow-sm text-red-600'
                        : 'text-neutral-600 hover:text-neutral-900'}"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        ><line x1="8" x2="21" y1="6" y2="6" /><line
                            x1="8"
                            x2="21"
                            y1="12"
                            y2="12"
                        /><line x1="8" x2="21" y1="18" y2="18" /><line
                            x1="3"
                            x2="3.01"
                            y1="6"
                            y2="6"
                        /><line x1="3" x2="3.01" y1="12" y2="12" /><line
                            x1="3"
                            x2="3.01"
                            y1="18"
                            y2="18"
                        /></svg
                    > List
                </button>
                <button
                    onclick={() => (viewMode = 'calendar')}
                    class="flex items-center gap-2 px-4 py-2 rounded-md font-semibold text-sm transition-all {viewMode ===
                    'calendar'
                        ? 'bg-white shadow-sm text-red-600'
                        : 'text-neutral-600 hover:text-neutral-900'}"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        ><rect
                            width="18"
                            height="18"
                            x="3"
                            y="4"
                            rx="2"
                            ry="2"
                        /><line x1="16" x2="16" y1="2" y2="6" /><line
                            x1="8"
                            x2="8"
                            y1="2"
                            y2="6"
                        /><line x1="3" x2="21" y1="10" y2="10" /><path
                            d="M8 14h.01"
                        /><path d="M12 14h.01" /><path d="M16 14h.01" /><path
                            d="M8 18h.01"
                        /><path d="M12 18h.01" /><path d="M16 18h.01" /></svg
                    > Calendar
                </button>
            </div>
        </div>
    </header>

    <section
        class="max-w-7xl mx-auto mb-6 bg-white p-5 rounded-xl border border-neutral-200 shadow-sm space-y-5"
    >
        <div class="flex flex-col md:flex-row gap-5">
            <div class="w-full md:w-1/4">
                <label
                    for="academicYear"
                    class="text-sm font-bold text-neutral-700 block mb-1.5"
                    >Academic Year</label
                >
                <select
                    id="academicYear"
                    bind:value={academicYear}
                    class="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none cursor-pointer"
                >
                    {#each availableYears as year}
                        <option value={year}>{year}</option>
                    {/each}
                </select>
            </div>

            <div class="w-full md:w-1/4">
                <label
                    for="cohort"
                    class="text-sm font-bold text-neutral-700 block mb-1.5"
                    >Cohort</label
                >
                <select
                    id="cohort"
                    bind:value={selectedCohort}
                    class="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none cursor-pointer"
                >
                    {#each cohorts as c}
                        <option value={c}>{c}</option>
                    {/each}
                </select>
            </div>

            <div class="w-full md:w-1/4">
                <label
                    for="search"
                    class="text-sm font-bold text-neutral-700 block mb-1.5"
                    >Search Period</label
                >
                <div class="relative">
                    <svg
                        class="absolute left-3 top-3 text-neutral-400"
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        ><circle cx="11" cy="11" r="8" /><line
                            x1="21"
                            x2="16.65"
                            y1="21"
                            y2="16.65"
                        /></svg
                    >
                    <input
                        id="search"
                        type="search"
                        placeholder="e.g. Semester 1..."
                        bind:value={searchQuery}
                        class="w-full pl-9 pr-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                    />
                </div>
            </div>

            <div class="w-full md:w-1/4 flex items-end pb-2">
                <label
                    class="flex items-center gap-3 cursor-pointer select-none group"
                >
                    <div class="relative flex items-center justify-center">
                        <input
                            type="checkbox"
                            bind:checked={intakesOnly}
                            class="peer sr-only"
                        />
                        <div
                            class="w-6 h-6 border-2 border-neutral-300 rounded peer-checked:bg-red-600 peer-checked:border-red-600 transition-colors"
                        ></div>
                        <svg
                            class="absolute text-white opacity-0 peer-checked:opacity-100 transition-opacity"
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="3"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            ><polyline points="20 6 9 17 4 12" /></svg
                        >
                    </div>
                    <span
                        class="text-sm font-semibold text-neutral-700 group-hover:text-neutral-900 transition-colors"
                        >Only show open intakes</span
                    >
                </label>
            </div>
        </div>

        <div class="border-t border-neutral-100 pt-4">
            <label class="text-sm font-bold text-neutral-700 block mb-2"
                >Toggle Period Types</label
            >
            <div class="flex flex-wrap gap-2">
                {#each periodTypes as type}
                    <button
                        onclick={() => (selectedType = type)}
                        class="px-4 py-1.5 rounded-full text-sm font-semibold border transition-all {selectedType ===
                        type
                            ? 'bg-neutral-800 text-white border-neutral-800 shadow-sm'
                            : 'bg-white text-neutral-600 border-neutral-300 hover:border-neutral-400 hover:bg-neutral-50'}"
                    >
                        {type}
                    </button>
                {/each}
            </div>
        </div>
    </section>

    <main aria-live="polite" class="max-w-7xl mx-auto">
        {#if viewMode === 'list'}
            {#if filteredData.length === 0}
                <div
                    class="text-center py-20 px-4 bg-white rounded-xl border border-neutral-200 border-dashed"
                >
                    <h3 class="text-lg font-semibold text-neutral-900">
                        No periods match your filters
                    </h3>
                </div>
            {:else}
                <div
                    class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                >
                    {#each filteredData as term (term.id)}
                        <article
                            class="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden flex flex-col relative"
                        >
                            <div class="p-5 pb-4 border-b border-neutral-100">
                                <div
                                    class="flex items-start justify-between mb-2"
                                >
                                    <span
                                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border {typeColors[
                                            term.type
                                        ] ||
                                            'bg-neutral-100 text-neutral-700 border-neutral-200'}"
                                        >{term.type}</span
                                    >
                                    {#if term.intake}
                                        <span
                                            class="text-[10px] uppercase font-bold tracking-wider text-emerald-700 bg-emerald-100 px-2 py-1 rounded"
                                            >Intake Open</span
                                        >
                                    {/if}
                                </div>
                                <h2 class="text-xl font-bold text-neutral-900">
                                    {term.period}
                                </h2>
                                <div
                                    class="flex justify-between items-center mt-1"
                                >
                                    <p class="text-xs text-neutral-500">
                                        {term.cohort}
                                    </p>
                                    {#if term.officialSourceUrl}
                                        <a
                                            href={term.officialSourceUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            class="text-xs text-blue-600 hover:underline"
                                            >Official PDF</a
                                        >
                                    {/if}
                                </div>
                            </div>

                            <div class="p-5 flex-grow space-y-4 text-sm">
                                <div class="flex justify-between items-center">
                                    <span class="text-neutral-500 font-medium"
                                        >Duration</span
                                    >
                                    <span
                                        class="text-neutral-900 font-bold text-right"
                                        ><time datetime={term.start}
                                            >{formatDate(term.start)}</time
                                        >
                                        <span class="text-neutral-300 px-1"
                                            >→</span
                                        >
                                        <time datetime={term.end}
                                            >{formatDate(term.end)}</time
                                        ></span
                                    >
                                </div>
                                <div
                                    class="flex justify-between items-center bg-red-50 -mx-5 px-5 py-3 border-y border-red-100"
                                >
                                    <span class="text-red-900 font-bold"
                                        >Census Date</span
                                    >
                                    <time
                                        datetime={term.census}
                                        class="text-red-900 font-bold bg-white px-2 py-1 rounded border border-red-200 shadow-sm"
                                        >{formatDate(term.census)}</time
                                    >
                                </div>
                                {#if term.fapStart}
                                    <div
                                        class="flex justify-between items-center pt-1"
                                    >
                                        <span
                                            class="text-neutral-500 font-medium"
                                            >Final Assessments</span
                                        >
                                        <span
                                            class="text-neutral-900 font-semibold text-right"
                                            ><time datetime={term.fapStart}
                                                >{formatDate(
                                                    term.fapStart,
                                                )}</time
                                            >
                                            <span class="text-neutral-300 px-1"
                                                >→</span
                                            >
                                            <time datetime={term.fapEnd}
                                                >{formatDate(term.fapEnd)}</time
                                            ></span
                                        >
                                    </div>
                                {/if}
                                {#if term.results}
                                    <div
                                        class="flex justify-between items-center pt-1"
                                    >
                                        <span
                                            class="text-neutral-500 font-medium"
                                            >Results Published</span
                                        >
                                        <time
                                            datetime={term.results}
                                            class="text-neutral-900 font-semibold"
                                            >{formatDate(term.results)}</time
                                        >
                                    </div>
                                {/if}
                            </div>
                        </article>
                    {/each}
                </div>
            {/if}
        {:else}
            <div
                class="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden"
            >
                <div
                    class="flex items-center justify-between p-4 border-b border-neutral-200 bg-neutral-50"
                >
                    <h2 class="text-2xl font-bold text-neutral-800">
                        {currentMonth.toLocaleDateString('en-AU', {
                            month: 'long',
                            year: 'numeric',
                        })}
                    </h2>
                    <div class="flex gap-2">
                        <button
                            onclick={prevMonth}
                            class="p-2 border border-neutral-300 rounded hover:bg-neutral-100 transition-colors"
                            ><svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                ><polyline points="15 18 9 12 15 6" /></svg
                            ></button
                        >
                        <button
                            onclick={nextMonth}
                            class="p-2 border border-neutral-300 rounded hover:bg-neutral-100 transition-colors"
                            ><svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                ><polyline points="9 18 15 12 9 6" /></svg
                            ></button
                        >
                    </div>
                </div>

                <div
                    class="grid grid-cols-7 border-b border-neutral-200 bg-neutral-50"
                >
                    {#each ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as day}
                        <div
                            class="py-3 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider border-r last:border-0 border-neutral-200"
                        >
                            {day}
                        </div>
                    {/each}
                </div>

                <div class="grid grid-cols-7 auto-rows-fr">
                    {#each Array(startOffset) as _}
                        <div
                            class="min-h-[140px] bg-neutral-50 border-r border-b border-neutral-100"
                        ></div>
                    {/each}

                    {#each Array(daysInMonth) as _, idx}
                        {@const day = idx + 1}
                        {@const activePeriods = filteredData.filter((term) =>
                            isDayInRange(term.start, term.end, day),
                        )}
                        {@const censusEvents = filteredData.filter((term) =>
                            isDateOnDay(term.census, day),
                        )}
                        {@const fapEvents = filteredData.filter(
                            (term) =>
                                term.fapStart &&
                                isDayInRange(term.fapStart, term.fapEnd, day),
                        )}
                        {@const resultEvents = filteredData.filter(
                            (term) =>
                                term.results && isDateOnDay(term.results, day),
                        )}

                        <div
                            class="min-h-[140px] border-r border-b border-neutral-200 p-1.5 flex flex-col gap-1 hover:bg-neutral-50 transition-colors group"
                        >
                            <span
                                class="text-sm font-bold w-7 h-7 flex items-center justify-center rounded-full mb-1 {new Date().getDate() ===
                                    day &&
                                new Date().getMonth() ===
                                    currentMonth.getMonth() &&
                                new Date().getFullYear() ===
                                    currentMonth.getFullYear()
                                    ? 'bg-red-600 text-white'
                                    : 'text-neutral-500 group-hover:text-neutral-900'}"
                                >{day}</span
                            >
                            <div
                                class="flex-grow space-y-1 overflow-y-auto max-h-[100px] scrollbar-thin"
                            >
                                {#each activePeriods as term}
                                    <div
                                        class="text-[10px] px-1.5 py-0.5 font-semibold truncate border {typeColors[
                                            term.type
                                        ]} rounded-sm shadow-sm"
                                        title={term.period}
                                    >
                                        {term.period}
                                    </div>
                                {/each}
                                {#each fapEvents as term}
                                    <div
                                        class="text-[10px] px-1.5 py-0.5 bg-neutral-800 text-white font-semibold rounded-sm truncate"
                                        title="FAP: {term.period}"
                                    >
                                        FAP: {term.period}
                                    </div>
                                {/each}
                                {#each censusEvents as term}
                                    <div
                                        class="flex items-center gap-1 text-[10px] font-bold text-red-700 bg-red-50 px-1 py-0.5 rounded border border-red-200"
                                    >
                                        <div
                                            class="w-1.5 h-1.5 bg-red-600 rounded-full shrink-0"
                                        ></div>
                                        <span class="truncate"
                                            >Census: {term.period}</span
                                        >
                                    </div>
                                {/each}
                                {#each resultEvents as term}
                                    <div
                                        class="flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded border border-emerald-200"
                                    >
                                        <div
                                            class="w-1.5 h-1.5 bg-emerald-600 rounded-full shrink-0"
                                        ></div>
                                        <span class="truncate"
                                            >Results: {term.period}</span
                                        >
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/each}

                    {#each Array((7 - ((startOffset + daysInMonth) % 7)) % 7) as _}
                        <div
                            class="min-h-[140px] bg-neutral-50 border-r border-b border-neutral-100"
                        ></div>
                    {/each}
                </div>
            </div>
        {/if}
    </main>

    <footer class="max-w-7xl mx-auto mt-12 mb-6 pt-6 border-t border-neutral-200 text-center text-sm text-neutral-500">
        <p class="mb-2">Made with ❤️ for Swinburne — By E. Ketterer</p>
        <p>
            <a href="https://github.com/Arziel1992/swinburne-easy-calendar" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">GitHub Repository</a>
            <span class="mx-2">&bull;</span>
            <a href="https://github.com/Arziel1992/swinburne-easy-calendar/blob/main/LICENSE" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">License</a>
        </p>
    </footer>
</div>
