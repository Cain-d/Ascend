export default function Dashboard() {
  const stats = {
    calories: 2250,
    protein: 165,
    carbs: 210,
    fats: 68,
  };

  const workout = {
    type: "Push (Chest/Triceps)",
    exercises: [
      { name: "Bench Press", sets: 4, reps: 8 },
      { name: "Incline DB Press", sets: 3, reps: 10 },
      { name: "Tricep Push-down", sets: 3, reps: 12 },
    ],
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-800 p-6">
      <h1 className="text-3xl font-bold text-center mb-8">Today</h1>

      <div className="grid grid-cols-2 gap-6 max-w-md mx-auto mb-8">
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <h2 className="font-semibold text-lg mb-2">Calories</h2>
          <p className="text-2xl font-bold">{stats.calories} kcal</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <h2 className="font-semibold text-lg mb-2">Protein</h2>
          <p className="text-2xl font-bold">{stats.protein} g</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <h2 className="font-semibold text-lg mb-2">Carbs</h2>
          <p className="text-2xl font-bold">{stats.carbs} g</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <h2 className="font-semibold text-lg mb-2">Fats</h2>
          <p className="text-2xl font-bold">{stats.fats} g</p>
        </div>
      </div>

      <div className="max-w-xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-4">
          Workout — {workout.type}
        </h2>
        <div className="bg-white rounded-xl shadow p-4 space-y-3">
          {workout.exercises.map((ex, index) => (
            <div key={index} className="flex justify-between border-b pb-1">
              <span>{ex.name}</span>
              <span>
                {ex.sets} × {ex.reps}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
